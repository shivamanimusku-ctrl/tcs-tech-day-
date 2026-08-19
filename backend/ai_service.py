"""AI service — generates explanations and recommendations via Claude API.

Calls the Anthropic Claude API with actual contributing data to generate
natural-language explanations and actionable recommendations.
Falls back gracefully if no API key is configured.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def _get_client():
    """Get Anthropic client, or None if not configured."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not ANTHROPIC_AVAILABLE:
        return None
    return anthropic.Anthropic(api_key=api_key)


def generate_explanation(alert_data: dict) -> str:
    """Generate a natural-language explanation of why the risk exists.
    
    Args:
        alert_data: dict with risk_score, risk_level, contributing_factors, business_impact, line_id, machine_id
    
    Returns:
        AI-generated explanation string, or fallback text.
    """
    client = _get_client()

    factors = alert_data.get("contributing_factors", [])
    if isinstance(factors, str):
        factors = json.loads(factors)

    impact = alert_data.get("business_impact", {})
    if isinstance(impact, str):
        impact = json.loads(impact)

    prompt = f"""You are a manufacturing plant early warning system. Based on the following sensor data and risk factors, write a concise 2-3 sentence explanation of why this machine/line is at risk. Reference specific numbers from the data. Be direct and factual.

Machine: {alert_data.get('machine_id', 'Unknown')}
Line: {alert_data.get('line_id', 'Unknown')}
Risk Score: {alert_data.get('risk_score', 0)}/100 ({alert_data.get('risk_level', 'Unknown')})

Contributing Factors:
{json.dumps(factors, indent=2)}

Business Impact:
- Units at risk: {impact.get('units_at_risk', 0)}
- Estimated cost: ${impact.get('estimated_cost', 0):,}
- Affected customer: {impact.get('affected_customer', 'N/A')}
- Order due: {impact.get('order_due_date', 'N/A')}
- Expected downtime: {impact.get('expected_downtime_hours', 0)} hours

Write ONLY the explanation, no headers or prefixes. Keep it under 100 words."""

    if client is None:
        return _generate_fallback_explanation(alert_data, factors, impact)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning(f"AI explanation call failed: {e}")
        return _generate_fallback_explanation(alert_data, factors, impact)


def generate_recommendations(alert_data: dict) -> str:
    """Generate 2-4 concrete action items based on contributing risk factors.
    
    Returns:
        AI-generated recommendations as a numbered list string.
    """
    client = _get_client()

    factors = alert_data.get("contributing_factors", [])
    if isinstance(factors, str):
        factors = json.loads(factors)

    impact = alert_data.get("business_impact", {})
    if isinstance(impact, str):
        impact = json.loads(impact)

    prompt = f"""You are a manufacturing plant early warning system. Based on the following risk factors, generate 2-4 specific, actionable recommendations. Each should be a concrete action tied to a specific contributing factor.

Machine: {alert_data.get('machine_id', 'Unknown')}
Line: {alert_data.get('line_id', 'Unknown')}
Risk Score: {alert_data.get('risk_score', 0)}/100 ({alert_data.get('risk_level', 'Unknown')})

Contributing Factors:
{json.dumps(factors, indent=2)}

Business Impact:
- Units at risk: {impact.get('units_at_risk', 0)}
- Estimated cost: ${impact.get('estimated_cost', 0):,}
- Affected customer: {impact.get('affected_customer', 'N/A')}
- Expected downtime: {impact.get('expected_downtime_hours', 0)} hours

Write each recommendation as a numbered item (1. 2. 3. etc.). Be specific — reference the machine ID, temperatures, vibration values, etc. Keep each item to one sentence. No headers or extra text."""

    if client is None:
        return _generate_fallback_recommendations(alert_data, factors)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning(f"AI recommendation call failed: {e}")
        return _generate_fallback_recommendations(alert_data, factors)


def _generate_fallback_explanation(alert_data: dict, factors: list, impact: dict) -> str:
    """Generate a rule-based fallback explanation when AI is unavailable."""
    parts = []
    machine = alert_data.get("machine_id", "Unknown")
    line = alert_data.get("line_id", "Unknown")
    score = alert_data.get("risk_score", 0)

    parts.append(f"{machine} on {line} has a risk score of {score}/100.")

    for f in factors:
        name = f.get("factor", "")
        if name == "Temperature Deviation":
            parts.append(
                f"Temperature is {f['value']}{f.get('unit','')} vs normal {f['normal']}{f.get('unit','')}"
                f" ({f['deviation_pct']}% deviation)."
            )
        elif name == "Vibration Deviation":
            parts.append(
                f"Vibration at {f['value']}{f.get('unit','')} vs normal {f['normal']}{f.get('unit','')}"
                f" ({f['deviation_pct']}% deviation)."
            )
        elif name == "Maintenance Overdue":
            parts.append(f"Maintenance is {f['value']}.")
        elif name == "Production Below Target":
            parts.append(
                f"Production at {f['value']}/{f['target']} units ({f['deviation_pct']}% below target)."
            )
        elif name == "Elevated Defect Rate":
            parts.append(f"Defect rate elevated at {f['value']}.")
        elif name == "Material Shortage":
            parts.append(f"Material shortage: {f.get('material','')} at {f.get('availability_pct',0)}% availability.")
        elif name == "Understaffed Shift":
            parts.append(f"Understaffed: {f.get('present',0)}/{f.get('scheduled',0)} operators on {f.get('shift','')} shift.")

    if impact.get("affected_customer"):
        parts.append(
            f"{impact['affected_customer']} order (due {impact.get('order_due_date','N/A')}) "
            f"at risk — ${impact.get('estimated_cost', 0):,} potential impact."
        )

    return " ".join(parts[:5])  # Cap length


def _generate_fallback_recommendations(alert_data: dict, factors: list) -> str:
    """Generate rule-based fallback recommendations."""
    recs = []
    machine = alert_data.get("machine_id", "Unknown")

    for f in factors:
        name = f.get("factor", "")
        if name == "Temperature Deviation":
            recs.append(f"1. Inspect {machine} cooling system — temperature {f['deviation_pct']}% above normal at {f['value']}{f.get('unit','')}.")
        elif name == "Vibration Deviation":
            recs.append(f"2. Check {machine} bearings and alignment — vibration at {f['value']}{f.get('unit','')} ({f['deviation_pct']}% above normal).")
        elif name == "Maintenance Overdue":
            recs.append(f"3. Schedule immediate preventive maintenance for {machine} — {f['value']}.")
        elif name == "Production Below Target":
            recs.append(f"4. Review {machine} operating parameters and reduce load to prevent further degradation.")
        elif name == "Elevated Defect Rate":
            recs.append(f"5. Increase quality inspection frequency and investigate defect root cause ({f['value']} defect rate).")
        elif name == "Material Shortage":
            recs.append(f"6. Expedite {f.get('material','')} procurement — stock at {f.get('availability_pct',0)}% of required quantity.")
        elif name == "Understaffed Shift":
            recs.append(f"7. Call in additional operators or redistribute workload — {f.get('present',0)}/{f.get('scheduled',0)} present.")

    if not recs:
        recs.append(f"1. Monitor {machine} closely and review sensor data trends.")
        recs.append(f"2. Conduct a visual inspection of {machine} during next scheduled break.")

    return "\n".join(recs[:4])


async def enrich_alerts_with_ai(alerts: list) -> list:
    """Enrich a list of alert dicts with AI-generated explanation and recommendations."""
    from database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    for alert in alerts:
        explanation = generate_explanation(alert)
        recommendations = generate_recommendations(alert)

        alert["ai_explanation"] = explanation
        alert["ai_recommendation"] = recommendations

        # Update in DB
        cursor.execute(
            "UPDATE alerts SET ai_explanation = ?, ai_recommendation = ?, updated_at = datetime('now') WHERE alert_id = ?",
            (explanation, recommendations, alert["alert_id"])
        )

    conn.commit()
    conn.close()
    return alerts

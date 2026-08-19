"""Risk scoring engine — computes risk scores for each line/machine.

Weights: Machine Health 40%, Maintenance Risk 30%, Production Deviation 30%.
Levels: 0-30 Low, 31-60 Medium, 61-80 High, 81-100 Critical.
"""

import json
import uuid
from datetime import datetime
from database import get_connection


def _risk_level(score: float) -> str:
    if score <= 30:
        return "Low"
    elif score <= 60:
        return "Medium"
    elif score <= 80:
        return "High"
    else:
        return "Critical"


def compute_machine_health_score(latest_reading: dict) -> tuple[float, list]:
    """Compute machine health component (0-40 max) from sensor readings."""
    factors = []

    if latest_reading is None:
        return 0, factors

    temp = latest_reading["temperature"]
    normal_temp = latest_reading["normal_temperature"]
    vib = latest_reading["vibration"]
    normal_vib = latest_reading["normal_vibration"]

    # Temperature deviation
    temp_dev_pct = abs(temp - normal_temp) / normal_temp * 100 if normal_temp > 0 else 0
    temp_score = min(50, temp_dev_pct * 1.5)

    # Vibration deviation
    vib_dev_pct = abs(vib - normal_vib) / normal_vib * 100 if normal_vib > 0 else 0
    vib_score = min(50, vib_dev_pct * 1.5)

    # Normalize to 0-40
    health_raw = (temp_score + vib_score) / 100 * 40

    if temp_dev_pct > 10:
        factors.append({
            "factor": "Temperature Deviation",
            "value": round(temp, 1),
            "normal": round(normal_temp, 1),
            "unit": "°C",
            "deviation_pct": round(temp_dev_pct, 1),
            "severity": "High" if temp_dev_pct > 20 else "Medium"
        })

    if vib_dev_pct > 10:
        factors.append({
            "factor": "Vibration Deviation",
            "value": round(vib, 2),
            "normal": round(normal_vib, 2),
            "unit": "mm/s",
            "deviation_pct": round(vib_dev_pct, 1),
            "severity": "High" if vib_dev_pct > 50 else "Medium"
        })

    return round(health_raw, 1), factors


def compute_maintenance_score(machine: dict) -> tuple[float, list]:
    """Compute maintenance risk component (0-30 max)."""
    factors = []

    if not machine.get("maintenance_due_date"):
        return 0, factors

    due_date = datetime.strptime(machine["maintenance_due_date"], "%Y-%m-%d")
    today = datetime.now()
    days_overdue = (today - due_date).days

    if days_overdue <= 0:
        # Not overdue, low risk based on proximity
        days_until = abs(days_overdue)
        if days_until < 7:
            score = 10
            factors.append({
                "factor": "Maintenance Due Soon",
                "value": f"{days_until} days remaining",
                "severity": "Low"
            })
        else:
            score = 0
        return score, factors

    # Overdue: scale up to 30
    overdue_score = min(30, days_overdue * 2.5)

    last_maint = machine.get("last_maintenance_date", "Unknown")
    factors.append({
        "factor": "Maintenance Overdue",
        "value": f"{days_overdue} days overdue",
        "last_maintenance": last_maint,
        "severity": "Critical" if days_overdue > 10 else "High"
    })

    return round(overdue_score, 1), factors


def compute_production_score(line_id: str, conn) -> tuple[float, list]:
    """Compute production deviation component (0-30 max)."""
    factors = []

    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM production_logs WHERE line_id = ? ORDER BY timestamp DESC LIMIT 1",
        (line_id,)
    )
    row = cursor.fetchone()
    if not row:
        return 0, factors

    target = row["production_target"]
    actual = row["actual_production"]
    deviation_pct = (target - actual) / target * 100 if target > 0 else 0

    if deviation_pct > 5:
        prod_score = min(30, deviation_pct * 2.2)
        factors.append({
            "factor": "Production Below Target",
            "value": actual,
            "target": target,
            "unit": "units",
            "deviation_pct": round(deviation_pct, 1),
            "severity": "High" if deviation_pct > 10 else "Medium"
        })
        return round(prod_score, 1), factors

    return 0, factors


def compute_additional_factors(line_id: str, machine_id: str, conn) -> list:
    """Gather additional contributing factors: quality, materials, staffing, notes."""
    factors = []
    cursor = conn.cursor()

    # Quality / defect rate
    cursor.execute(
        "SELECT * FROM quality_inspections WHERE line_id = ? ORDER BY timestamp DESC LIMIT 1",
        (line_id,)
    )
    quality = cursor.fetchone()
    if quality and quality["defect_rate"] > 0.03:
        factors.append({
            "factor": "Elevated Defect Rate",
            "value": f"{quality['defect_rate']*100:.1f}%",
            "defect_count": quality["defect_count"],
            "total_inspected": quality["total_inspected"],
            "severity": "High" if quality["defect_rate"] > 0.05 else "Medium"
        })

    # Materials shortage
    cursor.execute(
        "SELECT * FROM materials WHERE line_id = ? AND availability_pct < 50",
        (line_id,)
    )
    for mat in cursor.fetchall():
        factors.append({
            "factor": "Material Shortage",
            "material": mat["name"],
            "stock_level": mat["stock_level"],
            "required": mat["required_quantity"],
            "availability_pct": mat["availability_pct"],
            "severity": "High" if mat["availability_pct"] < 30 else "Medium"
        })

    # Staffing issues
    cursor.execute(
        "SELECT * FROM shifts WHERE line_id = ? AND date = ? ORDER BY shift_name",
        (line_id, datetime.now().strftime("%Y-%m-%d"))
    )
    for shift in cursor.fetchall():
        if shift["operators_present"] < shift["operators_scheduled"] * 0.8:
            factors.append({
                "factor": "Understaffed Shift",
                "shift": shift["shift_name"],
                "present": shift["operators_present"],
                "scheduled": shift["operators_scheduled"],
                "severity": "Medium"
            })

    # Operator notes
    cursor.execute(
        "SELECT * FROM issue_notes WHERE (line_id = ? OR machine_id = ?) ORDER BY timestamp DESC LIMIT 3",
        (line_id, machine_id)
    )
    for note in cursor.fetchall():
        factors.append({
            "factor": "Operator Note",
            "text": note["text"],
            "author": note["author_role"],
            "timestamp": note["timestamp"],
            "severity": "Info"
        })

    return factors


def compute_business_impact(line_id: str, risk_score: float, conn) -> dict:
    """Estimate business impact for an alert."""
    cursor = conn.cursor()

    # Get linked order
    cursor.execute(
        "SELECT * FROM production_orders WHERE line_id = ? ORDER BY due_date ASC LIMIT 1",
        (line_id,)
    )
    order = cursor.fetchone()

    # Get latest production
    cursor.execute(
        "SELECT * FROM production_logs WHERE line_id = ? ORDER BY timestamp DESC LIMIT 1",
        (line_id,)
    )
    prod = cursor.fetchone()

    impact = {
        "units_at_risk": 0,
        "estimated_cost": 0,
        "affected_line": line_id,
        "affected_order": None,
        "affected_customer": None,
        "order_due_date": None,
        "expected_downtime_hours": 0,
        "impact_score": 0,
    }

    unit_value = 45  # dollars per unit

    if order:
        remaining = order["units_target"] - order["units_completed"]
        impact["affected_order"] = order["order_id"]
        impact["affected_customer"] = order["customer"]
        impact["order_due_date"] = order["due_date"]
        impact["units_at_risk"] = remaining

    if prod:
        deviation_pct = (prod["production_target"] - prod["actual_production"]) / prod["production_target"] if prod["production_target"] > 0 else 0
        units_delayed = int(prod["production_target"] * deviation_pct)
        impact["units_at_risk"] = max(impact["units_at_risk"], units_delayed)

    # Estimate downtime based on risk
    if risk_score > 80:
        impact["expected_downtime_hours"] = 8
    elif risk_score > 60:
        impact["expected_downtime_hours"] = 4
    elif risk_score > 30:
        impact["expected_downtime_hours"] = 2
    else:
        impact["expected_downtime_hours"] = 0

    impact["estimated_cost"] = impact["units_at_risk"] * unit_value

    # Impact score for ranking (0-100)
    cost_normalized = min(100, impact["estimated_cost"] / 500)  # $50,000 = 100
    order_urgency = 0
    if order:
        days_until = (datetime.strptime(order["due_date"], "%Y-%m-%d") - datetime.now()).days
        if days_until <= 1:
            order_urgency = 40
        elif days_until <= 3:
            order_urgency = 20
        else:
            order_urgency = 5
    impact["impact_score"] = round(min(100, cost_normalized + order_urgency), 1)

    return impact


def generate_alerts():
    """Run the risk engine across all machines and generate/update alerts."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing alerts
    cursor.execute("DELETE FROM alerts")

    # Get all machines
    cursor.execute("SELECT * FROM machines")
    machines = [dict(row) for row in cursor.fetchall()]

    alerts = []
    for machine in machines:
        machine_id = machine["machine_id"]
        line_id = machine["line_id"]

        # Get latest reading
        cursor.execute(
            "SELECT * FROM machine_readings WHERE machine_id = ? ORDER BY timestamp DESC LIMIT 1",
            (machine_id,)
        )
        latest_reading = cursor.fetchone()
        latest_reading = dict(latest_reading) if latest_reading else None

        # Compute components
        health_score, health_factors = compute_machine_health_score(latest_reading)
        maint_score, maint_factors = compute_maintenance_score(machine)
        prod_score, prod_factors = compute_production_score(line_id, conn)
        additional_factors = compute_additional_factors(line_id, machine_id, conn)

        # Total risk score
        risk_score = round(min(100, health_score + maint_score + prod_score), 1)
        risk_level = _risk_level(risk_score)

        # All contributing factors
        all_factors = health_factors + maint_factors + prod_factors + additional_factors

        # Business impact
        business_impact = compute_business_impact(line_id, risk_score, conn)

        # Only create alert if there's meaningful risk
        if risk_score < 15 and not any(
            f["factor"] in ["Material Shortage", "Understaffed Shift"] for f in all_factors
        ):
            continue

        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()

        alerts.append({
            "alert_id": alert_id,
            "line_id": line_id,
            "machine_id": machine_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "contributing_factors": json.dumps(all_factors),
            "business_impact": json.dumps(business_impact),
            "status": "New",
            "created_at": now,
        })

    # Sort by composite score for ranking
    alerts.sort(key=lambda a: (
        a["risk_score"] * 0.6 +
        json.loads(a["business_impact"]).get("impact_score", 0) * 0.4
    ), reverse=True)

    # Assign priority ranks and rationale
    for rank, alert in enumerate(alerts, 1):
        alert["priority_rank"] = rank
        impact = json.loads(alert["business_impact"])
        if rank == 1:
            alert["priority_rationale"] = (
                f"{alert['machine_id']} on {alert['line_id']} should be addressed first — "
                f"highest risk score ({alert['risk_score']}) "
                f"and business impact (${impact.get('estimated_cost', 0):,} at risk"
                f"{', ' + impact.get('affected_customer', '') + ' order due ' + impact.get('order_due_date', '') if impact.get('affected_customer') else ''})."
            )
        else:
            alert["priority_rationale"] = (
                f"Priority #{rank}: Risk score {alert['risk_score']}, "
                f"${impact.get('estimated_cost', 0):,} estimated impact."
            )

    # Insert alerts
    for alert in alerts:
        cursor.execute("""
            INSERT INTO alerts (alert_id, line_id, machine_id, risk_score, risk_level,
                contributing_factors, business_impact, status, priority_rank,
                priority_rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["alert_id"], alert["line_id"], alert["machine_id"],
            alert["risk_score"], alert["risk_level"],
            alert["contributing_factors"], alert["business_impact"],
            alert["status"], alert["priority_rank"],
            alert["priority_rationale"], alert["created_at"],
        ))

    conn.commit()
    conn.close()
    return alerts

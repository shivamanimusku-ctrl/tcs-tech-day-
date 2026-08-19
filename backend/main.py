"""FastAPI main application — REST API for the Early Warning System."""

import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, init_db
from seed import seed_all
from risk_engine import generate_alerts
from ai_service import enrich_alerts_with_ai
from models import (
    MachineOut, ReadingOut, ProductionLogOut, QualityOut,
    MaterialOut, ShiftOut, IssueNoteOut, ProductionOrderOut,
    AlertOut, StatusUpdate, DashboardSummary,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and seed data on startup."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM machines")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        logger.info("No data found — seeding database...")
        seed_all()
        logger.info("Running risk engine...")
        alerts = generate_alerts()
        logger.info(f"Generated {len(alerts)} alerts, enriching with AI...")
        await enrich_alerts_with_ai(alerts)
        logger.info("Startup complete — dashboard ready.")
    else:
        logger.info(f"Database has {count} machines — skipping seed.")

    yield


app = FastAPI(
    title="AI-Enabled Production Disruption Early Warning System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ──────────────────────────────────────────────────────────────────

def _rows_to_dicts(cursor) -> list[dict]:
    return [dict(row) for row in cursor.fetchall()]


# ── Data Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/machines", response_model=list[MachineOut])
def get_machines():
    conn = get_connection()
    rows = _rows_to_dicts(conn.execute("SELECT * FROM machines"))
    conn.close()
    return rows


@app.get("/api/machines/{machine_id}/readings", response_model=list[ReadingOut])
def get_machine_readings(machine_id: str):
    conn = get_connection()
    rows = _rows_to_dicts(
        conn.execute("SELECT * FROM machine_readings WHERE machine_id = ? ORDER BY timestamp", (machine_id,))
    )
    conn.close()
    return rows


@app.get("/api/production", response_model=list[ProductionLogOut])
def get_production(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM production_logs WHERE line_id = ? ORDER BY timestamp DESC", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM production_logs ORDER BY timestamp DESC"))
    conn.close()
    return rows


@app.get("/api/quality", response_model=list[QualityOut])
def get_quality(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM quality_inspections WHERE line_id = ? ORDER BY timestamp DESC", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM quality_inspections ORDER BY timestamp DESC"))
    conn.close()
    return rows


@app.get("/api/materials", response_model=list[MaterialOut])
def get_materials(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM materials WHERE line_id = ?", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM materials"))
    conn.close()
    return rows


@app.get("/api/shifts", response_model=list[ShiftOut])
def get_shifts(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM shifts WHERE line_id = ?", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM shifts"))
    conn.close()
    return rows


@app.get("/api/notes", response_model=list[IssueNoteOut])
def get_notes(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM issue_notes WHERE line_id = ? ORDER BY timestamp DESC", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM issue_notes ORDER BY timestamp DESC"))
    conn.close()
    return rows


@app.get("/api/orders", response_model=list[ProductionOrderOut])
def get_orders(line_id: str = None):
    conn = get_connection()
    if line_id:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM production_orders WHERE line_id = ? ORDER BY due_date", (line_id,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM production_orders ORDER BY due_date"))
    conn.close()
    return rows


# ── Alert Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/alerts")
def get_alerts(status: str = None):
    conn = get_connection()
    if status:
        rows = _rows_to_dicts(
            conn.execute("SELECT * FROM alerts WHERE status = ? ORDER BY priority_rank", (status,))
        )
    else:
        rows = _rows_to_dicts(conn.execute("SELECT * FROM alerts ORDER BY priority_rank"))
    conn.close()

    # Parse JSON fields
    for row in rows:
        row["contributing_factors"] = json.loads(row.get("contributing_factors", "[]"))
        row["business_impact"] = json.loads(row.get("business_impact", "{}"))
    return rows


@app.post("/api/alerts/generate")
async def regenerate_alerts():
    """Re-run the risk engine and regenerate all alerts."""
    alerts = generate_alerts()
    await enrich_alerts_with_ai(alerts)
    return {"message": f"Generated {len(alerts)} alerts", "count": len(alerts)}


@app.patch("/api/alerts/{alert_id}/status")
def update_alert_status(alert_id: str, body: StatusUpdate):
    """Update alert status: New → Acknowledged → In Progress → Resolved."""
    valid_statuses = {"New", "Acknowledged", "In Progress", "Resolved", "Escalated"}
    if body.status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET status = ?, updated_at = ? WHERE alert_id = ?",
        (body.status, datetime.now().isoformat(), alert_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Alert not found")

    conn.commit()
    conn.close()
    return {"message": f"Alert {alert_id} updated to {body.status}"}


@app.post("/api/alerts/{alert_id}/escalate")
def escalate_alert(alert_id: str):
    """Escalate an alert."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET status = 'Escalated', updated_at = ? WHERE alert_id = ?",
        (datetime.now().isoformat(), alert_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Alert not found")

    conn.commit()
    conn.close()
    return {"message": f"Alert {alert_id} escalated"}


@app.post("/api/alerts/{alert_id}/regenerate-ai")
async def regenerate_ai_for_alert(alert_id: str):
    """Re-run AI explanation and recommendations for a single alert."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Alert not found")

    alert = dict(row)
    alert["contributing_factors"] = json.loads(alert.get("contributing_factors", "[]"))
    alert["business_impact"] = json.loads(alert.get("business_impact", "{}"))

    await enrich_alerts_with_ai([alert])
    return {"message": "AI content regenerated", "alert_id": alert_id}


# ── Dashboard Summary ──────────────────────────────────────────────────────

@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    conn = get_connection()

    # Total machines/lines
    machines = _rows_to_dicts(conn.execute("SELECT * FROM machines"))
    total_machines = len(machines)
    lines = set(m["line_id"] for m in machines)
    total_lines = len(lines)

    # Active alerts
    alerts = _rows_to_dicts(conn.execute("SELECT * FROM alerts WHERE status != 'Resolved'"))
    active_alerts = len(alerts)
    lines_at_risk = len(set(a["line_id"] for a in alerts))

    # Overall risk (avg of active alert scores)
    if alerts:
        avg_risk = sum(a["risk_score"] for a in alerts) / len(alerts)
    else:
        avg_risk = 0

    # Production health (avg of actual/target across latest logs per line)
    cursor = conn.execute("""
        SELECT line_id, actual_production, production_target 
        FROM production_logs 
        WHERE id IN (
            SELECT MAX(id) FROM production_logs GROUP BY line_id
        )
    """)
    prod_rows = _rows_to_dicts(cursor)
    if prod_rows:
        total_actual = sum(r["actual_production"] for r in prod_rows)
        total_target = sum(r["production_target"] for r in prod_rows)
        prod_health = (total_actual / total_target * 100) if total_target > 0 else 100
    else:
        prod_health = 100

    conn.close()

    return DashboardSummary(
        overall_risk_pct=round(avg_risk, 1),
        production_health_pct=round(prod_health, 1),
        active_alerts=active_alerts,
        lines_at_risk=lines_at_risk,
        total_lines=total_lines,
        total_machines=total_machines,
    )


# ── Seed/Reset ──────────────────────────────────────────────────────────────

@app.post("/api/seed")
async def reseed_database():
    """Re-seed the entire database and regenerate alerts."""
    seed_all()
    alerts = generate_alerts()
    await enrich_alerts_with_ai(alerts)
    return {"message": "Database reseeded and alerts regenerated", "alert_count": len(alerts)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""Seed script — populates all tables with the M103 deep scenario + 2 secondary issues.

Re-runnable: calling seed_all() resets the DB and repopulates everything.
"""

import uuid
from datetime import datetime, timedelta
from database import get_connection, reset_db


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _now():
    return datetime.now().isoformat()


def _hours_ago(h):
    return (datetime.now() - timedelta(hours=h)).isoformat()


def _days_ago(d):
    return (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")


def _tomorrow():
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def seed_all():
    """Reset DB and seed all tables."""
    reset_db()
    conn = get_connection()
    c = conn.cursor()

    # =========================================================================
    # MACHINES
    # =========================================================================
    machines = [
        ("M103", "Line-3", "Press Machine M103", "Hydraulic Press", "Running",
         _days_ago(42), _days_ago(12)),  # overdue: last maint 42 days ago, due 12 days ago
        ("M101", "Line-1", "CNC Mill M101", "CNC Machine", "Running",
         _days_ago(15), (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")),
        ("M104", "Line-4", "Assembly Robot M104", "Robotic Arm", "Running",
         _days_ago(20), (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")),
    ]
    c.executemany(
        "INSERT INTO machines VALUES (?,?,?,?,?,?,?)", machines
    )

    # =========================================================================
    # MACHINE READINGS — M103 trending up over past 8 hours
    # =========================================================================
    readings = []
    for i in range(8, -1, -1):
        # Temperature: 65 (normal) → 82 (now), linear ramp
        temp = 65 + (82 - 65) * ((8 - i) / 8)
        # Vibration: 2.1 (normal) → 4.2 (now), linear ramp
        vib = 2.1 + (4.2 - 2.1) * ((8 - i) / 8)
        readings.append((
            "M103", _hours_ago(i), round(temp, 1), round(vib, 2), 65.0, 2.1
        ))
    # M101 — normal readings
    for i in range(4, -1, -1):
        readings.append((
            "M101", _hours_ago(i), 58.0 + (i % 2), 1.8, 58.0, 1.8
        ))
    # M104 — normal readings
    for i in range(4, -1, -1):
        readings.append((
            "M104", _hours_ago(i), 45.0 + (i % 3), 1.2, 45.0, 1.2
        ))
    c.executemany(
        "INSERT INTO machine_readings (machine_id, timestamp, temperature, vibration, normal_temperature, normal_vibration) VALUES (?,?,?,?,?,?)",
        readings,
    )

    # =========================================================================
    # PRODUCTION LOGS — Line 3 falling behind, others normal
    # =========================================================================
    production = [
        # Line 3: target 500, actual 435 (~13% below)
        ("Line-3", _hours_ago(4), 500, 435, 25),
        ("Line-3", _hours_ago(2), 500, 440, 20),
        ("Line-3", _now(), 500, 430, 30),
        # Line 1: on target
        ("Line-1", _hours_ago(4), 600, 590, 5),
        ("Line-1", _hours_ago(2), 600, 595, 3),
        ("Line-1", _now(), 600, 585, 8),
        # Line 4: slightly below
        ("Line-4", _hours_ago(4), 400, 395, 2),
        ("Line-4", _hours_ago(2), 400, 390, 5),
        ("Line-4", _now(), 400, 380, 10),
    ]
    c.executemany(
        "INSERT INTO production_logs (line_id, timestamp, production_target, actual_production, downtime_minutes) VALUES (?,?,?,?,?)",
        production,
    )

    # =========================================================================
    # QUALITY INSPECTIONS
    # =========================================================================
    quality = [
        # Line 3: 9% defect rate
        ("Line-3", _hours_ago(3), 0.09, 18, 200, "Fail"),
        ("Line-3", _now(), 0.09, 22, 244, "Fail"),
        # Line 1: 1.5% — normal
        ("Line-1", _hours_ago(3), 0.015, 3, 200, "Pass"),
        ("Line-1", _now(), 0.018, 4, 222, "Pass"),
        # Line 4: 2% — normal
        ("Line-4", _hours_ago(3), 0.02, 4, 200, "Pass"),
        ("Line-4", _now(), 0.022, 5, 227, "Pass"),
    ]
    c.executemany(
        "INSERT INTO quality_inspections (line_id, timestamp, defect_rate, defect_count, total_inspected, result) VALUES (?,?,?,?,?,?)",
        quality,
    )

    # =========================================================================
    # MATERIALS — Line 1 has a shortage
    # =========================================================================
    materials_data = [
        ("MAT-301", "Line-3", "Steel Sheet Grade A", 850, 900, 94.4),
        ("MAT-101", "Line-1", "Aluminum Rod 6061", 120, 500, 24.0),  # SHORTAGE
        ("MAT-102", "Line-1", "Coolant Fluid", 40, 50, 80.0),
        ("MAT-401", "Line-4", "Solder Wire", 300, 320, 93.75),
    ]
    c.executemany(
        "INSERT INTO materials VALUES (?,?,?,?,?,?)", materials_data
    )

    # =========================================================================
    # SHIFTS — Line 4 is short-staffed
    # =========================================================================
    shifts_data = [
        ("SH-301", "Line-3", _today(), "Day", 8, 8),
        ("SH-302", "Line-3", _today(), "Night", 8, 7),
        ("SH-101", "Line-1", _today(), "Day", 6, 6),
        ("SH-401", "Line-4", _today(), "Day", 10, 6),   # SHORT-STAFFED: 6/10
        ("SH-402", "Line-4", _today(), "Night", 10, 8),
    ]
    c.executemany(
        "INSERT INTO shifts VALUES (?,?,?,?,?,?)", shifts_data
    )

    # =========================================================================
    # ISSUE NOTES — operator notes
    # =========================================================================
    notes = [
        ("NOTE-001", "Line-3", "M103", _hours_ago(2), "Operator",
         "Press making unusual clicking noise, worse than yesterday"),
        ("NOTE-002", "Line-1", None, _hours_ago(5), "Supervisor",
         "Aluminum rod stock critically low — supplier delayed, expected 2 days late"),
        ("NOTE-003", "Line-4", None, _hours_ago(3), "Supervisor",
         "Short-staffed on day shift — 4 operators called in sick, running at 60% capacity"),
    ]
    c.executemany(
        "INSERT INTO issue_notes VALUES (?,?,?,?,?,?)", notes
    )

    # =========================================================================
    # PRODUCTION ORDERS — Acme Corp order on Line 3
    # =========================================================================
    orders = [
        ("ORD-3001", "Line-3", "Acme Corp", _tomorrow(), "High", 2000, 1450),
        ("ORD-1001", "Line-1", "Beta Industries", (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), "Normal", 3000, 2400),
        ("ORD-4001", "Line-4", "Gamma Systems", (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "Normal", 1500, 1100),
    ]
    c.executemany(
        "INSERT INTO production_orders VALUES (?,?,?,?,?,?,?)", orders
    )

    conn.commit()
    conn.close()
    print("✅ Database seeded successfully with M103 scenario + 2 secondary issues.")


if __name__ == "__main__":
    seed_all()

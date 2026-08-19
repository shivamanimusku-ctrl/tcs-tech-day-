"""Database module — SQLite connection and schema DDL for all 9 tables."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "factory.db")


def get_connection():
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS machines (
            machine_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            machine_name TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Running',
            last_maintenance_date TEXT,
            maintenance_due_date TEXT
        );

        CREATE TABLE IF NOT EXISTS machine_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            vibration REAL NOT NULL,
            normal_temperature REAL NOT NULL,
            normal_vibration REAL NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );

        CREATE TABLE IF NOT EXISTS production_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            production_target INTEGER NOT NULL,
            actual_production INTEGER NOT NULL,
            downtime_minutes INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS quality_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            defect_rate REAL NOT NULL,
            defect_count INTEGER NOT NULL,
            total_inspected INTEGER NOT NULL,
            result TEXT NOT NULL DEFAULT 'Pass'
        );

        CREATE TABLE IF NOT EXISTS materials (
            material_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            name TEXT NOT NULL,
            stock_level REAL NOT NULL,
            required_quantity REAL NOT NULL,
            availability_pct REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shifts (
            shift_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            date TEXT NOT NULL,
            shift_name TEXT NOT NULL,
            operators_scheduled INTEGER NOT NULL,
            operators_present INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS issue_notes (
            note_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            machine_id TEXT,
            timestamp TEXT NOT NULL,
            author_role TEXT NOT NULL,
            text TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS production_orders (
            order_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            customer TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Normal',
            units_target INTEGER NOT NULL,
            units_completed INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            line_id TEXT NOT NULL,
            machine_id TEXT,
            risk_score REAL NOT NULL DEFAULT 0,
            risk_level TEXT NOT NULL DEFAULT 'Low',
            contributing_factors TEXT NOT NULL DEFAULT '[]',
            business_impact TEXT NOT NULL DEFAULT '{}',
            ai_explanation TEXT,
            ai_recommendation TEXT,
            status TEXT NOT NULL DEFAULT 'New',
            priority_rank INTEGER,
            priority_rationale TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
    """)

    conn.commit()
    conn.close()


def reset_db():
    """Drop all tables and recreate."""
    conn = get_connection()
    cursor = conn.cursor()
    tables = [
        "alerts", "issue_notes", "production_orders", "shifts",
        "materials", "quality_inspections", "production_logs",
        "machine_readings", "machines"
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()
    init_db()

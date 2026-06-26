"""
db.py — SQLite schema and data access for Saathi.

Security notes:
- All inputs are parameterized (no string-formatted SQL, prevents injection)
- Text fields are length-capped and stripped before storage
- No PII beyond what's needed for the demo (name, medication, timestamps)
"""

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "saathi.db"
MAX_TEXT_LEN = 280  # cap free-text fields to prevent abuse / storage bloat


def sanitize_text(value: str) -> str:
    """Strip, collapse whitespace, and cap length on any free-text input."""
    if not isinstance(value, str):
        raise ValueError("Expected string input")
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:MAX_TEXT_LEN]


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                family_contact TEXT
            );

            CREATE TABLE IF NOT EXISTS medications (
                med_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                time_of_day TEXT NOT NULL,  -- e.g. "08:00"
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS dose_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                med_id TEXT NOT NULL,
                taken_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,   -- e.g. "dose_missed", "checkin", "confused_query"
                detail TEXT,
                logged_at TEXT NOT NULL
            );
            """
        )


def get_medication_schedule(user_id: str):
    user_id = sanitize_text(user_id)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT med_id, name, time_of_day FROM medications WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def log_dose_taken(user_id: str, med_id: str):
    user_id = sanitize_text(user_id)
    med_id = sanitize_text(med_id)
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO dose_log (user_id, med_id, taken_at) VALUES (?, ?, ?)",
            (user_id, med_id, now),
        )
    return {"status": "logged", "med_id": med_id, "taken_at": now}


def log_activity(user_id: str, event_type: str, detail: str = ""):
    user_id = sanitize_text(user_id)
    event_type = sanitize_text(event_type)
    detail = sanitize_text(detail)
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO activity_log (user_id, event_type, detail, logged_at) VALUES (?, ?, ?, ?)",
            (user_id, event_type, detail, now),
        )


def get_recent_activity(user_id: str, days: int = 7):
    user_id = sanitize_text(user_id)
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT event_type, detail, logged_at FROM activity_log "
            "WHERE user_id = ? AND logged_at >= ? ORDER BY logged_at DESC",
            (user_id, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]


def seed_demo_data():
    """Populate a demo user so the agent has something to work with out of the box."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name, family_contact) VALUES (?, ?, ?)",
            ("demo_user", "Lakshmi Amma", "daughter_priya@example.com"),
        )
        conn.executemany(
            "INSERT OR IGNORE INTO medications (med_id, user_id, name, time_of_day) VALUES (?, ?, ?, ?)",
            [
                ("med_bp", "demo_user", "Blood Pressure Tablet", "08:00"),
                ("med_diabetes", "demo_user", "Metformin", "13:00"),
                ("med_vitamin", "demo_user", "Vitamin D", "20:00"),
            ],
        )


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print(f"Database initialized at {DB_PATH}")

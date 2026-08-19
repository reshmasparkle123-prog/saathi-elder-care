"""
db.py — CockroachDB schema and data access for Saathi.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

MAX_TEXT_LEN = 280
EMBED_MODEL = "models/text-embedding-004"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
CONN_STRING = os.environ["COCKROACH_CONN_STRING"]


def sanitize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected string input")
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:MAX_TEXT_LEN]


@contextmanager
def get_conn():
    conn = psycopg2.connect(CONN_STRING)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    pass


def get_medication_schedule(user_id: str):
    user_id = sanitize_text(user_id)
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT med_id, name, time_of_day FROM medications WHERE user_id = %s",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def log_dose_taken(user_id: str, med_id: str):
    user_id = sanitize_text(user_id)
    med_id = sanitize_text(med_id)
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dose_log (user_id, med_id, taken_at) VALUES (%s, %s, %s)",
                (user_id, med_id, now),
            )
    return {"status": "logged", "med_id": med_id, "taken_at": now.isoformat()}


def log_activity(user_id: str, event_type: str, detail: str = ""):
    user_id = sanitize_text(user_id)
    event_type = sanitize_text(event_type)
    detail = sanitize_text(detail)
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO activity_log (user_id, event_type, detail, logged_at) VALUES (%s, %s, %s, %s)",
                (user_id, event_type, detail, now),
            )


def get_recent_activity(user_id: str, days: int = 7):
    user_id = sanitize_text(user_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT event_type, detail, logged_at FROM activity_log "
                "WHERE user_id = %s AND logged_at >= %s ORDER BY logged_at DESC",
                (user_id, cutoff),
            )
            return [dict(r) for r in cur.fetchall()]


def save_conversation_turn(user_id: str, role: str, message: str):
    user_id = sanitize_text(user_id)
    role = sanitize_text(role)
    message = sanitize_text(message)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (user_id, role, message) VALUES (%s, %s, %s)",
                (user_id, role, message),
            )


def _embed(text: str):
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return result["embedding"]


def store_memory(user_id: str, content: str):
    user_id = sanitize_text(user_id)
    content = sanitize_text(content)
    embedding = _embed(content)
    vec_literal = "[" + ",".join(str(x) for x in embedding) + "]"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO memory_embeddings (user_id, content, embedding) "
                "VALUES (%s, %s, %s::VECTOR(768))",
                (user_id, content, vec_literal),
            )


def search_memory(user_id: str, query: str, top_k: int = 3):
    user_id = sanitize_text(user_id)
    query_embedding = _embed(sanitize_text(query))
    vec_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT content, created_at, embedding <-> %s::VECTOR(768) AS distance "
                "FROM memory_embeddings WHERE user_id = %s "
                "ORDER BY distance ASC LIMIT %s",
                (vec_literal, user_id, top_k),
            )
            return [dict(r) for r in cur.fetchall()]


def seed_demo_data():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id, name, family_contact) VALUES (%s, %s, %s) "
                "ON CONFLICT (user_id) DO NOTHING",
                ("demo_user", "Lakshmi Amma", "daughter_priya@example.com"),
            )
            cur.executemany(
                "INSERT INTO medications (med_id, user_id, name, time_of_day) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (med_id) DO NOTHING",
                [
                    ("med_bp", "demo_user", "Blood Pressure Tablet", "08:00"),
                    ("med_diabetes", "demo_user", "Metformin", "13:00"),
                    ("med_vitamin", "demo_user", "Vitamin D", "20:00"),
                ],
            )


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized on CockroachDB")

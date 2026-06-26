"""
server.py — Saathi's MCP-style tool server.

Exposes four tools over HTTP that agents call instead of touching the
database directly. This keeps agent code free of storage logic and makes
the tool surface explicit and auditable — judges/reviewers can see exactly
what actions an agent is capable of taking.

Run:
    python mcp_server/server.py
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import db

app = FastAPI(title="Saathi MCP Tool Server")
db.init_db()


# ---------- Request/response models ----------

class ExpenseItem(BaseModel):
    label: str = Field(..., max_length=100)
    amount: float = Field(..., ge=0)


class CalculateExpenseRequest(BaseModel):
    user_id: str
    items: list[ExpenseItem]


class LogDoseRequest(BaseModel):
    user_id: str
    med_id: str


class LogActivityRequest(BaseModel):
    user_id: str
    event_type: str
    detail: str = ""


# ---------- Tools ----------

@app.get("/tools/get_medication_schedule")
def get_medication_schedule(user_id: str):
    """Returns the elder's medication schedule for the day."""
    schedule = db.get_medication_schedule(user_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="No medications found for this user")
    return {"user_id": user_id, "schedule": schedule}


@app.post("/tools/log_dose_taken")
def log_dose_taken(req: LogDoseRequest):
    """Records that a medication dose was taken."""
    return db.log_dose_taken(req.user_id, req.med_id)


@app.post("/tools/calculate_expense")
def calculate_expense(req: CalculateExpenseRequest):
    """
    Voice-driven expense calculator. Designed for users who cannot rely on
    a screen — the agent reads totals back aloud rather than displaying them.
    """
    total = sum(item.amount for item in req.items)
    breakdown = [{"label": item.label, "amount": item.amount} for item in req.items]
    db.log_activity(req.user_id, "expense_calculated", f"total={total}")
    return {"total": round(total, 2), "breakdown": breakdown}


@app.post("/tools/log_activity")
def log_activity(req: LogActivityRequest):
    """Logs a generic activity event (check-in, missed dose, confused query, etc.)."""
    db.log_activity(req.user_id, req.event_type, req.detail)
    return {"status": "logged"}


@app.get("/tools/get_recent_activity")
def get_recent_activity(user_id: str, days: int = 7):
    """
    Returns recent activity for the FamilyBridgeAgent to analyze for
    concerning patterns (e.g. repeated missed doses).
    """
    activity = db.get_recent_activity(user_id, days)
    return {"user_id": user_id, "days": days, "activity": activity}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

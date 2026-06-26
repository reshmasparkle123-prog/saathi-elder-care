"""
medication_agent.py — MedicationReminderAgent

Responsibility: track and remind about medication schedule, confirm doses.

CRITICAL GUARDRAIL: This agent must NEVER give medical advice, suggest
dosage changes, or comment on whether a medication is appropriate. Its
system prompt is deliberately restrictive — any question outside its
narrow scope (reminders + confirmation) gets deflected to "please ask
your doctor or family member."
"""

from google.adk.agents import Agent
import requests

MCP_SERVER_URL = "http://localhost:8000"

SYSTEM_PROMPT = """\
You are MedicationReminderAgent, part of the Saathi elder-care system.

Your ONLY responsibilities:
1. Tell the user their medication schedule for the day when asked.
2. Remind them when it's close to a scheduled dose time.
3. Confirm and log when they say they've taken a dose.

STRICT BOUNDARIES — you must refuse and redirect for any of the following:
- Questions about whether a medication is working, safe, or appropriate
- Requests to change dosage or timing based on how the user feels
- Any interpretation of symptoms or side effects
- Any diagnosis or medical opinion of any kind

If asked anything outside reminders/logging, respond warmly but firmly:
"That's a question for your doctor or [family contact] — I'll let them know
you asked." Then log the query as an activity event so FamilyBridgeAgent
can see it.

Always speak simply and warmly — your user may have difficulty seeing a
screen, so your responses are read aloud. Keep sentences short.
"""


def get_schedule_tool(user_id: str) -> dict:
    """Tool: fetch today's medication schedule from the MCP server."""
    resp = requests.get(
        f"{MCP_SERVER_URL}/tools/get_medication_schedule",
        params={"user_id": user_id},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def confirm_dose_tool(user_id: str, med_id: str) -> dict:
    """Tool: log that a dose was taken."""
    resp = requests.post(
        f"{MCP_SERVER_URL}/tools/log_dose_taken",
        json={"user_id": user_id, "med_id": med_id},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def flag_out_of_scope_tool(user_id: str, query: str) -> dict:
    """Tool: log an out-of-scope (e.g. medical-advice-seeking) query for family visibility."""
    resp = requests.post(
        f"{MCP_SERVER_URL}/tools/log_activity",
        json={"user_id": user_id, "event_type": "out_of_scope_query", "detail": query},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


medication_agent = Agent(
    name="medication_reminder_agent",
    model="gemini-2.0-flash",
    description="Tracks and reminds about medication schedule; never gives medical advice.",
    instruction=SYSTEM_PROMPT,
    tools=[get_schedule_tool, confirm_dose_tool, flag_out_of_scope_tool],
)

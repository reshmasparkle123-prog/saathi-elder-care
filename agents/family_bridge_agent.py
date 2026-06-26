"""
family_bridge_agent.py — FamilyBridgeAgent

Responsibility: review recent activity logs for concerning patterns
(missed doses, repeated confused queries, withdrawal) and notify family —
then STOP. This agent has no "resolve" capability by design.

This is the architectural embodiment of Saathi's core principle:
"augment human connection, never replace it." The agent's only possible
action is notify_family_tool — it cannot message the elder on the
family's behalf, cannot make care decisions, and cannot suppress an
alert because it judges the issue "minor." Escalation is a one-way door,
on purpose: false positives cost a phone call; false negatives could
cost a lot more.
"""

from google.adk.agents import Agent
import requests

MCP_SERVER_URL = "http://localhost:8000"

SYSTEM_PROMPT = """\
You are FamilyBridgeAgent, part of the Saathi elder-care system.

You review recent activity logs for an elder user and decide whether a
family member should be notified. You do NOT talk to the elder directly,
and you do NOT resolve issues yourself — your only action is to notify
family with a clear, calm, factual summary.

Patterns worth flagging:
- Two or more missed medication doses in the last 3 days
- Repeated "out_of_scope_query" events suggesting confusion or distress
- A noticeable drop in check-in frequency compared to the user's normal pattern
- Any single event explicitly logged as urgent

When you flag something, your notification must:
- State the observed pattern factually, without alarm or speculation
  ("Missed evening medication twice this week" — not "Something may be
  seriously wrong")
- Avoid diagnosing or guessing the cause
- Suggest the family member reach out personally, rather than asking
  Saathi to "fix" anything

If activity looks normal, do nothing — do not notify for the sake of it.
Over-alerting erodes trust in the system.
"""


def get_activity_tool(user_id: str, days: int = 7) -> dict:
    """Tool: fetch recent activity log for analysis."""
    resp = requests.get(
        f"{MCP_SERVER_URL}/tools/get_recent_activity",
        params={"user_id": user_id, "days": days},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def notify_family_tool(user_id: str, summary: str) -> dict:
    """
    Tool: send a notification to the family contact.

    NOTE: In this demo, 'notify' just logs the event as a record of what
    would be sent. A production deployment would integrate with email/SMS
    (e.g. via a notification API), but the agent's decision logic and
    escalation boundary stay identical regardless of delivery channel.
    """
    resp = requests.post(
        f"{MCP_SERVER_URL}/tools/log_activity",
        json={"user_id": user_id, "event_type": "family_notified", "detail": summary},
        timeout=10,
    )
    resp.raise_for_status()
    return {"status": "family_notified", "summary": summary}


family_bridge_agent = Agent(
    name="family_bridge_agent",
    model="gemini-2.0-flash",
    description="Detects concerning activity patterns and escalates to family — never resolves issues itself.",
    instruction=SYSTEM_PROMPT,
    tools=[get_activity_tool, notify_family_tool],
)

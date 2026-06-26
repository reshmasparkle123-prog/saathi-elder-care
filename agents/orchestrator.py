"""
orchestrator.py — Routes incoming requests to the right specialized agent.

This is the multi-agent "brain" — it doesn't do domain work itself, it
classifies intent and hands off to medication_agent, voice_agent, or
family_bridge_agent. Run this as the main entry point for interactions.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from google.adk.agents import Agent
from medication_agent import medication_agent
from voice_agent import voice_agent
from family_bridge_agent import family_bridge_agent

ORCHESTRATOR_PROMPT = """\
You are Saathi's orchestrator. You receive a user's spoken request and
decide which specialist agent should handle it:

- medication_reminder_agent: anything about medicine schedule, reminders,
  or confirming a dose was taken
- voice_accessibility_agent: expense calculations, general voice-based
  requests, "read this to me" style asks
- family_bridge_agent: NOT triggered by direct user requests — this runs
  periodically/automatically to review activity, not by user request

Route the request to the right agent and return its response as-is. If a
request is ambiguous, default to voice_accessibility_agent for general
conversation, since it's built for natural, flowing interaction.

Never attempt to answer medical, dosage, or health-interpretation
questions yourself — always route those through medication_reminder_agent,
which is the only agent permitted to handle (and deflect) them.
"""

orchestrator = Agent(
    name="saathi_orchestrator",
    model="gemini-2.0-flash",
    description="Routes user requests to the appropriate Saathi specialist agent.",
    instruction=ORCHESTRATOR_PROMPT,
    sub_agents=[medication_agent, voice_agent, family_bridge_agent],
)


def run_family_bridge_check(user_id: str = "demo_user"):
    """
    Periodic job (e.g. run daily via Cloud Scheduler in production) that
    triggers FamilyBridgeAgent to review activity and notify family if needed.
    This is intentionally separate from the user-facing orchestrator flow.
    """
    from google.adk.runners import Runner

    runner = Runner(agent=family_bridge_agent)
    result = runner.run(f"Review the last 7 days of activity for user_id={user_id} and notify family if needed.")
    return result


if __name__ == "__main__":
    from google.adk.runners import Runner

    print("Saathi orchestrator starting. Type a request (or 'quit'):")
    runner = Runner(agent=orchestrator)
    while True:
        user_input = input("> ")
        if user_input.lower() in ("quit", "exit"):
            break
        response = runner.run(user_input)
        print(response)

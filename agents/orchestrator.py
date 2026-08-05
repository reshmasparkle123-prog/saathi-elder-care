import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from medication_agent import medication_agent
from voice_agent import voice_agent
from family_bridge_agent import family_bridge_agent

ORCHESTRATOR_PROMPT = """\
You are Saathi's orchestrator. Route requests to the right agent:
- medication_reminder_agent: medicine schedule, reminders
- voice_accessibility_agent: general voice requests
- family_bridge_agent: automatic only, not user-triggered
"""

orchestrator = Agent(
    name="saathi_orchestrator",
    model="gemini-2.0-flash",
    description="Routes user requests to the appropriate Saathi specialist agent.",
    instruction=ORCHESTRATOR_PROMPT,
    sub_agents=[medication_agent, voice_agent, family_bridge_agent],
)

async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="saathi", user_id="demo_user", session_id="s1")
    runner = Runner(agent=orchestrator, session_service=session_service, app_name="saathi")
    print("Saathi orchestrator starting. Type a request (or 'quit'):")
    while True:
        user_input = input("> ")
        if user_input.lower() in ("quit", "exit"):
            break
        msg = Content(role="user", parts=[Part(text=user_input)])
        async for event in runner.run_async(user_id="demo_user", session_id="s1", new_message=msg):
            print(f"EVENT: {event}")

if __name__ == "__main__":
    asyncio.run(main())

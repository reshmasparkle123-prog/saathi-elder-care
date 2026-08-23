"""
chat_server.py — FastAPI wrapper around the Saathi ADK orchestrator.
Run:
    python agents/chat_server.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from pydantic import BaseModel
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

app = FastAPI(title="Saathi Orchestrator Chat Server")

session_service = InMemorySessionService()
runner = Runner(agent=orchestrator, session_service=session_service, app_name="saathi")

_known_sessions = set()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str = "s1"


@app.post("/chat")
async def chat(req: ChatRequest):
    key = (req.user_id, req.session_id)
    if key not in _known_sessions:
        await session_service.create_session(
            app_name="saathi", user_id=req.user_id, session_id=req.session_id
        )
        _known_sessions.add(key)

    msg = Content(role="user", parts=[Part(text=req.message)])
    response_text = ""
    async for event in runner.run_async(
        user_id=req.user_id, session_id=req.session_id, new_message=msg
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return {"response": response_text or "Sorry, I didn't catch that."}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

"""
chat_api.py — Thin FastAPI wrapper so the voice frontend can POST to the
orchestrator over HTTP. Keeps the agent runtime decoupled from the web layer.

Run alongside mcp_server/server.py:
    python agents/chat_api.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator import orchestrator
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

app = FastAPI(title="Saathi Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

APP_NAME = "saathi"
session_service = InMemorySessionService()
runner = Runner(agent=orchestrator, app_name=APP_NAME, session_service=session_service)


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = f"session_{req.user_id}"

    try:
        await session_service.create_session(
            app_name=APP_NAME, user_id=req.user_id, session_id=session_id
        )
    except Exception:
        pass

    content = types.Content(role="user", parts=[types.Part(text=req.message)])

    response_text = ""
    async for event in runner.run_async(
        user_id=req.user_id, session_id=session_id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    response_text += part.text

    return {"response": response_text}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

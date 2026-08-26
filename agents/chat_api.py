import os
from dotenv import load_dotenv
load_dotenv()
import json
import sqlite3
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware      
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Saathi Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DB_PATH = Path(__file__).parent.parent / "data" / "saathi.db"
DB_PATH.parent.mkdir(exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, medicine TEXT, time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS family_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def build_system_prompt(language: str) -> str:
    base = """You are Saathi, a warm, patient voice-first AI companion for elderly users.
You help with medication reminders, simple daily tasks, arithmetic, and staying connected to family.
Never give medical advice or diagnoses — only track reminders the user asks for.
When a user asks you to remind them about medicine, use the set_reminder tool.
When a user wants family to know they're okay, use the notify_family tool.
When a user asks a simple math/expense question, use the calculate tool.
You never resolve family concerns yourself — you only pass the message along and step back."""

    if language == "hi":
        lang_rule = "Always reply in Hinglish (a natural mix of Hindi and English), regardless of what language the user writes in. Speak simply and kindly."
    else:
        lang_rule = "Always reply in plain English only, with no Hindi words at all, regardless of what language the user writes in. Speak simply and kindly."

    return f"{base}\n{lang_rule}"


TOOLS = [
    {"type": "function", "function": {
        "name": "set_reminder",
        "description": "Store a medication reminder for the user",
        "parameters": {"type": "object", "properties": {
            "medicine": {"type": "string"}, "time": {"type": "string"}},
            "required": ["medicine", "time"]}}},
    {"type": "function", "function": {
        "name": "notify_family",
        "description": "Send an update to the user's family members",
        "parameters": {"type": "object", "properties": {
            "message": {"type": "string"}}, "required": ["message"]}}},
    {"type": "function", "function": {
        "name": "calculate",
        "description": "Perform a simple arithmetic calculation, e.g. for expenses",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "e.g. '45 + 30' or '120 / 4'"}},
            "required": ["expression"]}}},
]


def set_reminder(user_id, medicine, time):
    conn = get_db()
    conn.execute("INSERT INTO reminders (user_id, medicine, time) VALUES (?, ?, ?)",
                 (user_id, medicine, time))
    conn.commit()
    conn.close()
    return f"Reminder set: {medicine} at {time}"


def notify_family(user_id, message):
    conn = get_db()
    conn.execute("INSERT INTO family_updates (user_id, message) VALUES (?, ?)",
                 (user_id, message))
    conn.commit()
    conn.close()
    return f"Family notified: {message}"


def calculate(expression):
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Sorry, I can only do simple arithmetic."
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception:
        return "Sorry, I couldn't calculate that."


class ChatRequest(BaseModel):
    user_id: str
    message: str
    language: str = "en"


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        system_prompt = build_system_prompt(req.language)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message},
        ]
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b", messages=messages,
            tools=TOOLS, tool_choice="auto",
        )
        msg = completion.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments)
                if call.function.name == "set_reminder":
                    result = set_reminder(req.user_id, args["medicine"], args["time"])
                elif call.function.name == "notify_family":
                    result = notify_family(req.user_id, args["message"])
                elif call.function.name == "calculate":
                    result = calculate(args["expression"])
                else:
                    result = "Unknown tool"
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            followup = client.chat.completions.create(
                model="openai/gpt-oss-120b", messages=messages)
            return {"response": followup.choices[0].message.content}

        return {"response": msg.content}
    except Exception as e:
        print(f"Error in /chat: {e}")
        fallback = "Sorry, something went wrong. Please try again." if req.language == "en" else "Maaf kijiye, kuch gadbad ho gayi. Please try again."
        return {"response": fallback}


@app.get("/reminders/{user_id}")
def get_reminders(user_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT medicine, time, created_at FROM reminders WHERE user_id=? ORDER BY id DESC",
        (user_id,)).fetchall()
    conn.close()
    return [{"medicine": r[0], "time": r[1], "created_at": r[2]} for r in rows]


@app.get("/family-updates/{user_id}")
def get_family_updates(user_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT message, created_at FROM family_updates WHERE user_id=? ORDER BY id DESC",
        (user_id,)).fetchall()
    conn.close()
    return [{"message": r[0], "created_at": r[1]} for r in rows]


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)   

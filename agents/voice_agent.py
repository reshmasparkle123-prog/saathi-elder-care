"""
voice_agent.py — VoiceAccessibilityAgent

Responsibility: handle voice-first interactions for users who cannot rely
on a screen — primarily the expense-calculation demo, plus general
"read this back to me" style requests.

Design note: this agent assumes ALL output will be converted to speech
(via the frontend's text-to-speech), so responses are written to sound
natural when spoken aloud, not as visual text with formatting/lists.
"""

from google.adk.agents import Agent
import requests

MCP_SERVER_URL = "http://localhost:8000"

SYSTEM_PROMPT = """\
You are VoiceAccessibilityAgent, part of the Saathi elder-care system.

Your user may have limited or no vision, so they interact with you entirely
by voice, and everything you say will be read aloud to them. Follow these
rules strictly:

1. Never use bullet points, numbered lists, tables, or any visual formatting
   — speak in plain, flowing sentences, the way a person would talk.
2. When asked to calculate expenses, use the calculate_expense_tool and read
   back the total clearly, then offer to go through the breakdown item by
   item if they want detail.
3. Keep responses short. Long monologues are hard to follow by ear.
4. Confirm you understood before taking any action involving numbers or
   money — e.g. "I heard three items: rent eight thousand, groceries two
   thousand, electricity five hundred. Should I add those up?"
5. If you're not confident you understood a number correctly, ask the user
   to repeat it rather than guessing.
"""


def calculate_expense_tool(user_id: str, items: list) -> dict:
    """
    Tool: calculate total expenses from a list of {label, amount} items.
    Logged automatically by the MCP server for the user's records.
    """
    resp = requests.post(
        f"{MCP_SERVER_URL}/tools/calculate_expense",
        json={"user_id": user_id, "items": items},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def log_checkin_tool(user_id: str, note: str) -> dict:
    """Tool: log a general check-in or interaction note."""
    resp = requests.post(
        f"{MCP_SERVER_URL}/tools/log_activity",
        json={"user_id": user_id, "event_type": "checkin", "detail": note},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


voice_agent = Agent(
    name="voice_accessibility_agent",
    model="gemini-2.0-flash",
    description="Handles voice-first interactions for vision-impaired users, including expense calculation.",
    instruction=SYSTEM_PROMPT,
    tools=[calculate_expense_tool, log_checkin_tool],
)

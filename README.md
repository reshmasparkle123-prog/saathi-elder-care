# Saathi — AI Elder-Care Concierge Agent

**Kaggle Capstone Submission — Concierge Agents Track**
*5-Day AI Agents: Intensive Vibe Coding Course with Google*

## Problem

Elderly people — especially those with declining vision or hearing — struggle with
daily logistics: remembering medication, performing simple tasks (like calculating
expenses) without relying on a screen, and staying meaningfully connected to family
who can't always be physically present.

## Design Principle: Augment, Never Replace

Saathi is explicitly designed to strengthen real human connection, not substitute
for it. The `FamilyBridgeAgent` has no ability to "resolve" anything — its only
action is to notify a real family member when something looks concerning, then
step back.

## Architecture

Three agents, orchestrated with Google's Agent Development Kit (ADK), communicate
with a custom MCP server that exposes medication, activity, and calculation tools.

```
saathi/
├── agents/
│   ├── medication_agent.py     # MedicationReminderAgent
│   ├── voice_agent.py          # VoiceAccessibilityAgent
│   ├── family_bridge_agent.py  # FamilyBridgeAgent
│   └── orchestrator.py         # Routes requests to the right agent
├── mcp_server/
│   ├── server.py               # FastAPI + MCP server
│   └── db.py                   # SQLite schema + helpers
├── frontend/
│   └── index.html              # Voice-first web UI (Web Speech API)
├── data/
│   └── saathi.db                # SQLite DB (created on first run)
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your-ai-studio-api-key"   # never commit this
python mcp_server/server.py        # starts MCP server on :8000
python agents/orchestrator.py      # starts agent runtime
```

Open `frontend/index.html` in a browser (or serve it) to interact via voice.

## Security Notes

- No API keys are hardcoded — all secrets loaded from environment variables
- All user inputs (voice transcriptions, manual entries) are sanitized before
  being passed to tools or stored in the database
- Saathi never gives medical advice, dosage recommendations, or diagnoses —
  this is enforced at the system-prompt level in `medication_agent.py`
- Activity logs are stored locally (SQLite) for the demo; a production version
  would use encrypted storage and explicit user/family consent flows

## Course Concepts Demonstrated

| Concept | Where |
|---|---|
| Multi-agent system (ADK) | `agents/` — 3 specialized agents + orchestrator |
| MCP Server | `mcp_server/server.py` — exposes 4 tools |
| Security features | Guardrails in `medication_agent.py`, input sanitization in `db.py` |
| Deployability | `Dockerfile` + Cloud Run deployment (see below) |

## Deployment (Cloud Run)

```bash
gcloud run deploy saathi-backend --source . --region us-central1 --allow-unauthenticated
```

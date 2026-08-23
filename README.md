# Saathi — AI Elder-Care Concierge Agent

Saathi is a voice-first AI elder care concierge agent designed to help elderly users, particularly those with declining vision or hearing, manage everyday logistics: remembering medications, performing simple tasks without depending on a screen, and staying meaningfully connected to family who cannot always be physically present.

## Tech Stack
- **Backend:** FastAPI
- **LLM:** Groq LLaMA 3.3-70B (native tool-calling)
- **Storage:** SQLite (local, demo-scale)
- **Frontend:** Lightweight HTML/JavaScript chat interface (demo.html), extensible to full voice via the Web Speech API
- **Server:** Uvicorn

## How It Works
A user's natural-language message is sent to a FastAPI backend, which forwards it — along with a system prompt defining Saathi's persona and constraints — to Groq-hosted LLaMA 3.3-70B. The model is given two callable tools: `set_reminder` and `notify_family`. When a request matches one of these intents, the model issues a tool call, the backend executes the corresponding function, persists the result to SQLite, and returns a natural-language confirmation.

## Security & Design Principles
- No API keys are hardcoded — all secrets loaded from environment variables
- Saathi never gives medical advice or diagnoses — enforced at the system-prompt level
- The family-notification tool never resolves a concern on Saathi's behalf — it only logs and surfaces the update to a real family member
- Activity data is stored locally in SQLite for demonstration; production would use encrypted, access-controlled storage

## Quick Start
```bash
pip install -r requirements.txt
export GROQ_API_KEY="your-key"   # never commit this
python mcp_server/server.py       # tool server on :8000
python agents/chat_api.py         # chat API on :8001
cd frontend && python3 -m http.server 3000
```
Open `http://localhost:3000/demo.html` in your browser.

## About

Voice-first multilingual AI concierge for elderly users.

## Future Scope
Full voice input/output via Web Speech API, reconnecting to a dedicated MCP server, splitting into distinct ADK-orchestrated agents, encrypted production storage, and scheduled SMS/WhatsApp delivery to family.




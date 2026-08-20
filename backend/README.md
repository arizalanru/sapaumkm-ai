# GlowMart Sapa AI Backend

FastAPI service for the GlowMart customer-service prototype. It stores products, orders, FAQs, conversations, and messages in SQLite. Seed records are inserted automatically when each table is empty.

## Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Add a Groq key only to the local `backend/.env` file. Without one, deterministic database-backed replies keep the demo functional.

Chat responses include `response_mode`: `groq` for a successful Groq answer,
`deterministic` for database/rule-based output (including operation without an
API key), and `fallback_error` when a Groq or frontend request fails and the
safe fallback is used.

Run tests with:

```powershell
pytest
```

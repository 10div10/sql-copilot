# NL2SQL

Natural language → SQL platform. Upload a CSV or connect Postgres/MySQL, ask questions in plain English, get validated SQL + results.

## Flow
Frontend (NL question) → embed question → RAG retrieves relevant tables from schema (Chroma) → FastAPI builds prompt with schema + dialect → Groq LLM generates SQL → sqlglot validates (blocks non-SELECT, checks tables exist, enforces row limit) → executes against DB → self-correction retry on failure → plain-language answer.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --break-system-packages

export GROQ_API_KEY="your_key_here"
uvicorn main:app --reload --port 8000
```

Open `frontend/index.html` in a browser (or serve it).

## Endpoints
- `POST /upload` — upload CSV, builds SQLite dataset + schema index
- `POST /connect` — connect existing Postgres/MySQL DB via SQLAlchemy conn string
- `POST /query` — ask a question, returns `{sql, columns, rows, answer}`

## Notes
- Only SELECT statements are ever executed (sql_guard.py blocks DROP/DELETE/UPDATE/etc.)
- RAG (Chroma + bge-small embeddings) only kicks in past 6 tables — small schemas get full context, no retrieval overhead
- One LLM self-correction retry on execution error
- Read-only DB user recommended in production for the Postgres/MySQL connection string

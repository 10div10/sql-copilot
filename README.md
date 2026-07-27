# SQL Copilot

[![CI](https://github.com/10div10/sql-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/10div10/sql-copilot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)]()

Natural language → SQL. Upload a CSV or connect a Postgres/MySQL database, ask a question in plain English, get validated SQL and results back.

## How it works

```
NL question
  → embed question (bge-small-en-v1.5)
  → RAG retrieval of relevant tables from schema index (ChromaDB)
  → prompt built with schema context + target SQL dialect
  → Groq (llama-3.3-70b) generates SQL
  → sqlglot validates: blocks non-SELECT statements, rejects hallucinated
    tables/columns, enforces a row limit, transpiles to the target dialect
  → executed against the DB (read-only)
  → on execution error, one LLM self-correction retry
  → plain-language answer generated from the results
```

RAG only kicks in once a schema has more than 6 tables — smaller schemas get the full schema in the prompt directly, skipping retrieval overhead.

## Stack

- **Backend:** FastAPI
- **LLM:** Groq (`llama-3.3-70b-versatile`)
- **SQL validation:** sqlglot
- **Schema RAG:** ChromaDB + sentence-transformers (`bge-small-en-v1.5`)
- **DB support:** SQLite (from uploaded CSV), Postgres, MySQL via SQLAlchemy
- **Frontend:** static HTML/JS (no framework), talks to the FastAPI backend directly

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export GROQ_API_KEY="your_key_here"
uvicorn main:app --reload --port 8000
```

Open `frontend/index.html` in a browser.

Get a free Groq API key at [console.groq.com](https://console.groq.com) — no credit card required.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/upload` | POST | Upload a CSV, builds a SQLite dataset + indexes its schema |
| `/connect` | POST | Connect an existing Postgres/MySQL DB via SQLAlchemy connection string |
| `/query` | POST | Ask a question. Returns `{sql, columns, rows, answer}` |
| `/health` | GET | Health check |

## Safety

- Only `SELECT` statements are ever executed — `sql_guard.py` parses and rejects `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`.
- Generated SQL is checked against the known schema before execution — hallucinated tables/columns are rejected, not silently run.
- A row limit is enforced on every query if the LLM doesn't add one.
- For production Postgres/MySQL connections, use a read-only DB user.

## Tests

```bash
cd backend
pip install pytest httpx
export GROQ_API_KEY=dummy
pytest tests/ -v
```

Covers: SQL guard rejection of destructive/hallucinated/malformed queries, CSV → SQLite loading, and the health endpoint. Runs automatically on every push via GitHub Actions.

## Project structure

```
backend/
  main.py            FastAPI app - /upload, /connect, /query
  db.py               engine setup for sqlite/postgres/mysql, CSV loader
  schema_store.py      schema introspection + Chroma RAG index
  sql_guard.py         sqlglot-based validation and dialect transpilation
  llm.py               Groq calls: generate SQL, self-correct, explain results
  tests/
frontend/
  index.html           upload/connect UI, question box, results view
```

## License

MIT

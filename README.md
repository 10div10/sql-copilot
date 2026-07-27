# SQL Copilot — Interactive README

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![Status](https://img.shields.io/badge/status-draft-yellow)]()
[![Run Demo](https://img.shields.io/badge/run-demo-local-brightgreen)]()

SQL Copilot translates natural-language questions into SQL and helps you run, test, and iterate on queries safely. This README includes a small interactive demo you can run locally to try NL→SQL conversion and execute queries on a sample dataset.

Quick highlights
- Interactive local demo (Streamlit) to try NL→SQL conversion and query an example SQLite DB.
- Support for plugging in your LLM (OpenAI, other APIs) or using a simple fallback translator for offline demos.
- Safety notes and recommended .gitignore entries to avoid committing secrets or DB dumps.

Live / Interactive demo (local)
1. Install dependencies
   pip install -r requirements.txt
   pip install streamlit

   Optional (LLM mode):
   pip install openai python-dotenv

2. Copy environment example and add API key if you want to use an LLM:
   cp .env.example .env
   # set OPENAI_API_KEY or other provider key in .env

3. Run the playground:
   streamlit run interactive/playground.py

4. In the demo:
   - Enter a natural-language request (e.g. "List top 5 customers by revenue in 2024").
   - Click "Translate" to show the generated SQL.
   - Click "Run SQL" to execute it against an in-memory sample SQLite DB and view results.

Why this README is "interactive"
- It ships a lightweight Streamlit playground so reviewers and maintainers can try NL→SQL without provisioning a DB or keys.
- The playground supports two modes:
  - LLM mode (requires API key) — demonstrates production-style usage.
  - Fallback mode (no key) — shows a deterministic / heuristic conversion so the demo always runs offline.

Quickstart (CLI)
- Translate and print SQL (example CLI wrapper):
  python -m sql_copilot.cli --nl "Give me the top 10 orders by amount"

- Run the local Streamlit demo:
  streamlit run interactive/playground.py

Playground (what the demo does)
- Builds a small example SQLite DB (tables: customers, orders, products).
- Shows schema and sample rows.
- Accepts a NL question and:
  - If OPENAI_API_KEY (or other provider env var) is present, calls the provider to convert NL→SQL using a safe prompt template that includes schema and execution constraints.
  - Otherwise uses a conservative heuristic fallback to create a simple SELECT query or asks the user to refine the request.
- Executes SQL and displays results in a table with an execution trace.

Security / Safety
- Never commit real DB dumps, credentials, or production data to this repo.
- Add these to `.gitignore`:
  - .env
  - *.db
  - data/
  - dbs/
  - models/
  - checkpoints/
  - logs/
- When using external LLMs, sanitize or avoid sending sensitive data to third-party APIs. Prefer local models or private endpoints for regulated data.

Contributing
- Please add tests for any new translator logic.
- Keep example/data generation deterministic (seeded random) so demos are reproducible.
- If adding new provider integrations, add an example provider config to `docs/providers.md` (do not include secrets).

Troubleshooting
- If you see errors in playground:
  - Ensure Python >= 3.8 is used.
  - If using LLM mode, confirm OPENAI_API_KEY is set and you have network access.
  - If streamlit is slow, reduce the sample DB size or run with fewer UI widgets.

License & Contact
- MIT License (or choose appropriate license).
- Maintainer: @10div10 — open issues or PRs for improvements.

import os
import re
from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_TEMPLATE = """You are an expert SQL generator for {dialect}.
Given a user's natural language question and the relevant schema below,
write ONE syntactically correct {dialect} SELECT query that answers it.

Rules:
- Only output SELECT statements. Never write/alter data.
- Use only tables/columns that appear in the schema below. Do not invent columns.
- Prefer explicit column lists over SELECT * when reasonable.
- Return ONLY the SQL query, no markdown fences, no explanation.

Schema:
{schema_context}
"""


def generate_sql(nl_query: str, schema_context: str, dialect: str, model: str = "llama-3.3-70b-versatile") -> str:
    system = SYSTEM_TEMPLATE.format(dialect=dialect, schema_context=schema_context)
    resp = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": nl_query},
        ],
        temperature=0,
        max_tokens=500,
    )
    sql = resp.choices[0].message.content.strip()
    # strip stray markdown fences if the model adds them anyway
    sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()
    return sql


def explain_results(nl_query: str, sql: str, columns: list[str], rows: list[tuple], model: str = "llama-3.3-70b-versatile") -> str:
    preview = rows[:5]
    prompt = (
        f"User asked: {nl_query}\nSQL run: {sql}\n"
        f"Result columns: {columns}\nFirst rows: {preview}\n"
        "In 1-2 short sentences, answer the user's question in plain language using these results."
    )
    resp = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150,
    )
    return resp.choices[0].message.content.strip()


def self_correct_sql(nl_query: str, schema_context: str, dialect: str, bad_sql: str, error: str, model: str = "llama-3.3-70b-versatile") -> str:
    system = SYSTEM_TEMPLATE.format(dialect=dialect, schema_context=schema_context)
    prompt = (
        f"The previous query failed.\nQuestion: {nl_query}\n"
        f"Previous SQL: {bad_sql}\nError: {error}\n"
        "Fix it and return only the corrected SQL."
    )
    resp = _client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,
    )
    sql = resp.choices[0].message.content.strip()
    return re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()

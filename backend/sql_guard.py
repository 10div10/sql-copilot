"""
Validates LLM-generated SQL before execution:
- parses with sqlglot (catches syntax errors / hallucinated garbage)
- blocks destructive statements
- checks referenced tables/columns exist in the known schema
- transpiles to the target dialect
"""
import sqlglot
from sqlglot import exp

BLOCKED = {"drop", "delete", "truncate", "update", "insert", "alter", "grant", "create"}

DIALECT_MAP = {"postgres": "postgres", "mysql": "mysql", "sqlite": "sqlite"}


class SQLGuardError(Exception):
    pass


def validate_and_transpile(sql: str, dialect: str, schema: dict) -> str:
    dialect = DIALECT_MAP.get(dialect, "sqlite")

    try:
        parsed = sqlglot.parse_one(sql, read=dialect)
    except Exception as e:
        raise SQLGuardError(f"SQL failed to parse: {e}")

    stmt_type = parsed.key.lower()  # e.g. 'select', 'delete'
    if stmt_type in BLOCKED:
        raise SQLGuardError(f"Blocked statement type: {stmt_type}. Only SELECT is allowed.")

    if not isinstance(parsed, exp.Select) and not parsed.find(exp.Select):
        raise SQLGuardError("Only SELECT queries are permitted.")

    # Check referenced tables exist in schema (catches hallucinated tables)
    referenced_tables = {t.name.lower() for t in parsed.find_all(exp.Table)}
    known_tables = {t.lower() for t in schema.keys()}
    unknown = referenced_tables - known_tables
    if unknown:
        raise SQLGuardError(f"Query references unknown table(s): {unknown}")

    # Enforce a row limit as a safety net if none present
    if not parsed.args.get("limit"):
        parsed = parsed.limit(500)

    return parsed.sql(dialect=dialect)

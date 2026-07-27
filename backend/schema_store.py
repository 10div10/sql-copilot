"""
Introspects a DB (or SQLite dataset), builds per-table text descriptions,
embeds them, stores in Chroma for RAG retrieval so we don't dump the full
schema into every prompt.
"""
import chromadb
from sqlalchemy import inspect
from sentence_transformers import SentenceTransformer

_embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
_client = chromadb.Client()


def _embed(texts: list[str]) -> list[list[float]]:
    return _embedder.encode(texts, normalize_embeddings=True).tolist()


def build_schema_index(engine, session_id: str) -> dict:
    """
    Inspects the connected DB, builds a text blurb per table
    (table name, columns+types, FKs, 3 sample rows), embeds it,
    and stores it in a per-session Chroma collection.
    Returns the raw schema dict too (used for validation).
    """
    insp = inspect(engine)
    schema: dict = {}
    docs, ids = [], []

    for table in insp.get_table_names():
        cols = insp.get_columns(table)
        fks = insp.get_foreign_keys(table)
        pk = insp.get_pk_constraint(table).get("constrained_columns", [])

        col_desc = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
        fk_desc = "; ".join(
            f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
            for fk in fks
        )

        sample = ""
        try:
            with engine.connect() as conn:
                rows = conn.exec_driver_sql(f"SELECT * FROM {table} LIMIT 3").fetchall()
                sample = str(rows)
        except Exception:
            pass

        schema[table] = {
            "columns": [{"name": c["name"], "type": str(c["type"])} for c in cols],
            "primary_key": pk,
            "foreign_keys": fk_desc,
        }

        doc = (
            f"Table: {table}\nColumns: {col_desc}\n"
            f"Primary key: {pk}\nForeign keys: {fk_desc}\nSample rows: {sample}"
        )
        docs.append(doc)
        ids.append(table)

    coll = _client.get_or_create_collection(f"schema_{session_id}")
    # reset any stale entries for this session
    existing = coll.get()["ids"]
    if existing:
        coll.delete(ids=existing)

    if docs:
        coll.add(documents=docs, embeddings=_embed(docs), ids=ids)

    return schema


def retrieve_relevant_tables(nl_query: str, session_id: str, top_k: int = 4) -> list[str]:
    """RAG step: return the most relevant table docs for this NL question."""
    coll = _client.get_or_create_collection(f"schema_{session_id}")
    if coll.count() == 0:
        return []
    q_emb = _embed([nl_query])[0]
    n = min(top_k, coll.count())
    res = coll.query(query_embeddings=[q_emb], n_results=n)
    return res["documents"][0]

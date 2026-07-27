import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from db import make_engine, load_csv_to_sqlite, DATA_DIR
from schema_store import build_schema_index, retrieve_relevant_tables
from sql_guard import validate_and_transpile, SQLGuardError
from llm import generate_sql, explain_results, self_correct_sql

app = FastAPI(title="NL2SQL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> {"engine": Engine, "schema": dict, "dialect": str}
SESSIONS: dict = {}


class ConnectRequest(BaseModel):
    session_id: str
    platform: str  # 'postgres' | 'mysql' | 'sqlite'
    conn_str: str | None = None


class QueryRequest(BaseModel):
    session_id: str
    question: str
    use_rag: bool = True


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV -> becomes a SQLite dataset for this session."""
    session_id = str(uuid.uuid4())
    tmp_path = os.path.join(DATA_DIR, f"_tmp_{session_id}.csv")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    load_csv_to_sqlite(tmp_path, session_id)
    os.remove(tmp_path)

    engine = make_engine("sqlite", session_id=session_id)
    schema = build_schema_index(engine, session_id)

    SESSIONS[session_id] = {"engine": engine, "schema": schema, "dialect": "sqlite"}
    return {"session_id": session_id, "platform": "sqlite", "tables": list(schema.keys())}


@app.post("/connect")
def connect_db(req: ConnectRequest):
    """Connect to an existing Postgres/MySQL DB, or start a fresh sqlite session."""
    engine = make_engine(req.platform, req.conn_str, req.session_id)
    schema = build_schema_index(engine, req.session_id)
    SESSIONS[req.session_id] = {"engine": engine, "schema": schema, "dialect": req.platform}
    return {"session_id": req.session_id, "platform": req.platform, "tables": list(schema.keys())}


@app.post("/query")
def query(req: QueryRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Upload a dataset or connect a DB first.")

    engine, schema, dialect = session["engine"], session["schema"], session["dialect"]

    # RAG: retrieve relevant tables if schema is large, else use full schema
    if req.use_rag and len(schema) > 6:
        schema_context = "\n\n".join(retrieve_relevant_tables(req.question, req.session_id))
    else:
        schema_context = "\n\n".join(
            f"Table: {t}\nColumns: {[c['name'] for c in v['columns']]}"
            for t, v in schema.items()
        )

    sql = generate_sql(req.question, schema_context, dialect)

    try:
        safe_sql = validate_and_transpile(sql, dialect, schema)
    except SQLGuardError as e:
        raise HTTPException(400, f"Generated SQL rejected: {e}")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(safe_sql))
            columns = list(result.keys())
            rows = [tuple(r) for r in result.fetchall()]
    except Exception as e:
        # one self-correction retry
        corrected = self_correct_sql(req.question, schema_context, dialect, safe_sql, str(e))
        try:
            safe_sql = validate_and_transpile(corrected, dialect, schema)
            with engine.connect() as conn:
                result = conn.execute(text(safe_sql))
                columns = list(result.keys())
                rows = [tuple(r) for r in result.fetchall()]
        except Exception as e2:
            raise HTTPException(400, f"Query failed after retry: {e2}")

    answer = explain_results(req.question, safe_sql, columns, rows)

    return {
        "sql": safe_sql,
        "columns": columns,
        "rows": rows,
        "answer": answer,
    }


@app.get("/health")
def health():
    return {"status": "ok"}

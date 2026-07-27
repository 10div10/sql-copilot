import os
import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploaded_data")
os.makedirs(DATA_DIR, exist_ok=True)


def make_engine(platform: str, conn_str: str | None = None, session_id: str | None = None):
    """
    platform: 'postgres' | 'mysql' | 'sqlite'
    conn_str: full SQLAlchemy-style connection string for postgres/mysql,
              e.g. postgresql+psycopg2://user:pass@host:5432/dbname
    If platform == 'sqlite' and no conn_str, uses the uploaded dataset for this session.
    """
    if platform == "postgres":
        if not conn_str:
            raise ValueError("conn_str required for postgres")
        return create_engine(conn_str)
    if platform == "mysql":
        if not conn_str:
            raise ValueError("conn_str required for mysql")
        return create_engine(conn_str)
    # sqlite / no platform given -> use uploaded dataset
    db_path = os.path.join(DATA_DIR, f"{session_id}.db")
    return create_engine(f"sqlite:///{db_path}")


def load_csv_to_sqlite(file_path: str, session_id: str, table_name: str = "dataset") -> str:
    """Loads an uploaded CSV into a per-session SQLite DB. Returns the db path."""
    db_path = os.path.join(DATA_DIR, f"{session_id}.db")
    engine = create_engine(f"sqlite:///{db_path}")
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    return db_path

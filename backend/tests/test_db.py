import sys
import os
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import make_engine, load_csv_to_sqlite
from sqlalchemy import text


def test_sqlite_engine_creates(tmp_path):
    session_id = "test_session_1"
    engine = make_engine("sqlite", session_id=session_id)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    assert engine is not None


def test_csv_loads_into_sqlite(tmp_path):
    csv_path = tmp_path / "sample.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "amount"])
        writer.writerow([1, 100])
        writer.writerow([2, 200])

    session_id = "test_session_2"
    load_csv_to_sqlite(str(csv_path), session_id)

    engine = make_engine("sqlite", session_id=session_id)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT COUNT(*) FROM dataset")).fetchone()
    assert rows[0] == 2

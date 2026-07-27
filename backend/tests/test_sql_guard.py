import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sql_guard import validate_and_transpile, SQLGuardError

SCHEMA = {
    "dataset": {
        "columns": [{"name": "id", "type": "INTEGER"}, {"name": "amount", "type": "FLOAT"}],
        "primary_key": ["id"],
        "foreign_keys": "",
    }
}


def test_valid_select_passes():
    sql = "SELECT id, amount FROM dataset LIMIT 10"
    result = validate_and_transpile(sql, "sqlite", SCHEMA)
    assert "SELECT" in result.upper()


def test_blocks_drop():
    with pytest.raises(SQLGuardError):
        validate_and_transpile("DROP TABLE dataset", "sqlite", SCHEMA)


def test_blocks_delete():
    with pytest.raises(SQLGuardError):
        validate_and_transpile("DELETE FROM dataset WHERE id = 1", "sqlite", SCHEMA)


def test_blocks_update():
    with pytest.raises(SQLGuardError):
        validate_and_transpile("UPDATE dataset SET amount = 0", "sqlite", SCHEMA)


def test_rejects_unknown_table():
    with pytest.raises(SQLGuardError):
        validate_and_transpile("SELECT * FROM nonexistent_table", "sqlite", SCHEMA)


def test_rejects_garbage_sql():
    with pytest.raises(SQLGuardError):
        validate_and_transpile("this is not sql at all !!!", "sqlite", SCHEMA)


def test_adds_limit_when_missing():
    sql = "SELECT id FROM dataset"
    result = validate_and_transpile(sql, "sqlite", SCHEMA)
    assert "LIMIT" in result.upper()


def test_preserves_existing_limit():
    sql = "SELECT id FROM dataset LIMIT 5"
    result = validate_and_transpile(sql, "sqlite", SCHEMA)
    assert "LIMIT 5" in result.upper()

import json
import os


SCHEMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "schemas")
)


def test_event_schema_required_fields():
    schema_path = os.path.join(SCHEMA_DIR, "event.schema.json")
    with open(schema_path, "r") as schema_file:
        schema = json.load(schema_file)

    required = set(schema.get("required", []))
    assert {"id", "user_id", "event_type", "amount", "region", "source"}.issubset(required)


def test_parquet_schema_has_event_columns():
    parquet_path = os.path.join(SCHEMA_DIR, "event.parquet.json")
    with open(parquet_path, "r") as schema_file:
        schema = json.load(schema_file)

    columns = {col["name"] for col in schema.get("columns", [])}
    assert {"id", "user_id", "event_type", "amount", "region", "source"}.issubset(columns)

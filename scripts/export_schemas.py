"""Export versioned public domain JSON Schemas."""

from pathlib import Path

from ai_ops.domain.schemas import export_json_schemas

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    export_json_schemas(str(ROOT / "schemas"))
    print("SCHEMA_EXPORT_PASS schemas=11")

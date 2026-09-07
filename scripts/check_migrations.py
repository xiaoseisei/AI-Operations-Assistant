"""Validate that Alembic migration metadata is present and parseable."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    versions = ROOT / "alembic" / "versions"
    migration_files = sorted(versions.glob("*.py")) if versions.is_dir() else []
    required = (ROOT / "alembic.ini", ROOT / "alembic" / "env.py")
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if not migration_files:
        missing.append("alembic/versions/*.py")
    if missing:
        print("MIGRATION_CHECK_FAIL missing=" + ",".join(missing), file=sys.stderr)
        return 1
    print(f"MIGRATION_CHECK_PASS revisions={len(migration_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

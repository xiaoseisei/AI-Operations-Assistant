"""Static infrastructure checks that do not require a running Docker daemon."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.yaml"
REQUIRED = (
    "postgres@sha256:e62fbf9d3e2b49816a32c400ed2dba83e3b361e6833e624024309c35d334b412",
    "redis@sha256:bb142a9c18ac18a16713c1491d779697b4e107c22a97266616099d288237ef47",
    "minio/minio@sha256:9535594ad4122b7a78c6632788a989b96d9199b483d3bd71a5ceae73a922cdfa",
)


def main() -> int:
    text = COMPOSE.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED if item not in text]
    if missing or "networks:" not in text or "volumes:" not in text:
        print(f"INFRA_CHECK_FAIL missing={missing}", file=sys.stderr)
        return 1
    if re.search(r"(?:postgres|redis|minio[^\s]*)[:/]latest(?:\s|$)", text):
        print("INFRA_CHECK_FAIL latest image tag is forbidden", file=sys.stderr)
        return 1
    print("INFRA_CHECK_PASS fixed_digests=3 named_volumes=present backend_network=present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

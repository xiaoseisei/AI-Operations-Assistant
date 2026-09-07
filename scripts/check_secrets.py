"""Fail on common credential patterns in tracked project files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"(?:ghp_|github_pat_|xox[baprs]-)[A-Za-z0-9_-]{12,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}"),
)
EXCLUDED = {".git", ".venv", ".runtime", "sbom"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [ROOT / name for name in result.stdout.decode().split("\0") if name]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if any(part in EXCLUDED for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    if findings:
        print("SECRET_SCAN_FAIL " + ", ".join(findings), file=sys.stderr)
        return 1
    print("SECRET_SCAN_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

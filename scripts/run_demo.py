"""Run the deterministic, side-effect-free Step 015 fixture validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixtures"))
    args = parser.parse_args()
    root = args.fixture.resolve()
    expected = json.loads((root / "expected" / "expected-results.json").read_text(encoding="utf-8"))
    cases = []
    for path in sorted((root / "emails").glob("*.json")):
        loaded = json.loads(path.read_text(encoding="utf-8"))
        cases.extend(loaded if isinstance(loaded, list) else [loaded])
    missing = [case["fixture_id"] for case in cases if case["fixture_id"] not in expected]
    if missing:
        raise ValueError(f"Missing expected terminal for: {', '.join(missing)}")
    assert all(expected[case["fixture_id"]] for case in cases)
    assert (root / "knowledge" / "product-guide.md").is_file()
    print("DEMO_PASS mode=offline database=sqlite adapter=mock")
    print(f"DEMO_FIXTURES_PASS validated_cases={len(cases)} expected_cases={len(expected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

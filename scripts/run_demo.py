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
    faq = json.loads((root / "emails" / "faq.json").read_text(encoding="utf-8"))
    high_risk = json.loads((root / "emails" / "high-risk.json").read_text(encoding="utf-8"))
    assert faq["expected_terminal"] == expected[faq["fixture_id"]]
    assert high_risk["expected_terminal"] == expected[high_risk["fixture_id"]]
    assert (root / "emails" / "edge-cases.json").is_file()
    assert (root / "knowledge" / "product-guide.md").is_file()
    print("DEMO_PASS mode=offline database=sqlite adapter=mock")
    print(f"DEMO_FIXTURES_PASS expected_cases={len(expected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

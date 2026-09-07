"""Validate the Step 008 repository skeleton without importing providers."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "src" / "ai_ops"

REQUIRED_PACKAGES = (
    "api",
    "domain",
    "graphs",
    "agents",
    "skills",
    "tools",
    "connectors",
    "knowledge",
    "memory",
    "application",
    "infrastructure",
)
REQUIRED_TEST_DIRS = ("unit", "integration", "contract", "fixtures")
FORBIDDEN_PROVIDER_MODULES = {
    "googleapiclient",
    "openai",
    "langchain",
    "langgraph",
    "feishu",
    "imaplib",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"PASS {message}")


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    try:
        check(PACKAGE_ROOT.is_dir(), "src/ai_ops exists")
        check((PACKAGE_ROOT / "__init__.py").is_file(), "src/ai_ops package entry exists")
        check((PACKAGE_ROOT / "domain" / "interfaces.py").is_file(), "provider interfaces exist")
        for package in REQUIRED_PACKAGES:
            path = PACKAGE_ROOT / package
            check(path.is_dir(), f"package directory exists: {package}")
            check((path / "__init__.py").is_file(), f"package entry exists: {package}")
        for test_dir in REQUIRED_TEST_DIRS:
            check((ROOT / "tests" / test_dir).is_dir(), f"test directory exists: {test_dir}")
        check((ROOT / "deploy").is_dir(), "deploy directory exists")
        contract = ROOT / "tests" / "contract" / "test_provider_interfaces.py"
        check(contract.is_file(), "provider contract test exists")

        source_files = sorted(PACKAGE_ROOT.rglob("*.py"))
        for source_file in source_files:
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
            forbidden = imported_roots(tree) & FORBIDDEN_PROVIDER_MODULES
            check(not forbidden, f"no provider SDK imports: {source_file.relative_to(ROOT)}")

        print("SKELETON_CHECK_PASS")
        return 0
    except (OSError, SyntaxError, RuntimeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

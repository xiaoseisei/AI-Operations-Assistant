# Repository Guidelines

## Project Structure & Module Organization

This repository is currently documentation-first. All project materials live under `docs/`:

- `docs/README.md` is the entry point and status index.
- `docs/01-一期范围冻结.md` through `docs/05-数据分类与威胁模型.md` define the Level 0 baseline.
- `docs/superpowers/specs/` stores approved design specifications.
- `docs/superpowers/plans/` stores implementation plans.
- `scripts/` contains cross-platform health checks and the offline fixture.
- `compose.yaml` and `compose.dev.yaml` define the optional container boundary.
- `src/ai_ops/` contains the layered application package; `tests/` is split into unit, integration, contract, and fixture areas.
- `deploy/` contains deployment materials; `scripts/check_skeleton.py` validates Step 008 boundaries.
- `sbom/` contains the generated CycloneDX dependency inventory; `scripts/generate_sbom.ps1` and `scripts/generate_sbom.sh` regenerate it.

The repository now has a minimal `pyproject.toml` environment baseline and a Step 008 package skeleton, but provider implementations and business workflows are not present yet. Keep adapters, workflow code, persistence, and tests in clearly separated directories and update this guide as implementation grows.

## Build, Test, and Development Commands

From the repository root, use these environment checks:

```powershell
rg --files -g '!docs/superpowers/**'
git diff --check -- .
pwsh -NoProfile -File scripts/healthcheck.ps1
docker compose -f compose.yaml -f compose.dev.yaml config
```

For the Step 1–5 acceptance suite, follow the PowerShell checks in `docs/superpowers/plans/2026-09-04-email-ops-foundation-plan.md`; they verify required links, task IDs, UAT counts, ADRs, threats, and secret-like patterns.

Step 007 details, version floors, offline fallback, and path rules are documented in `docs/06-开发环境基线.md`.

Step 008 skeleton validation: `python scripts/check_skeleton.py`. Provider SDK imports belong in `src/ai_ops/connectors/`; Graph and domain modules must remain provider-neutral.

Step 009 dependency and quality checks: `uv lock --check`, `uv sync --locked --dev`, `uv run ruff check src tests scripts`, `uv run mypy src`, `uv run pytest -q`, `uv run pip-audit`, and `pwsh -NoProfile -File scripts/generate_sbom.ps1`. Regenerate `sbom/cyclonedx-python.json` whenever `uv.lock` changes.

## Coding Style & Naming Conventions

Use Markdown with concise headings, tables, fenced code blocks, and Mermaid diagrams where a flow is clearer visually. Use UTF-8, no trailing whitespace, and stable identifiers: `TASK-001`, `UAT-H-001`, `UAT-E-001`, `ADR-001`, and `T-001`. Numbered Chinese filenames should remain stable once referenced. Keep policy terms and state names exact, such as `PENDING_APPROVAL`, `HUMAN_REVIEW`, `SEND_UNKNOWN`, and `QUARANTINED`.

## Testing Guidelines

Until runtime code exists, validation is document-based. UAT documents must contain at least 20 happy-path and 20 exception scenarios, each with `Given`, `When`, `Then`, and evidence assertions for database/Graph state, audit events, and adapter results. Do not treat HTTP 200 alone as proof of an external side effect.

## Commit & Pull Request Guidelines

Use focused Conventional Commit messages, for example `docs: add email task contracts and risk matrix`. Keep unrelated parent-repository changes out of commits. Pull requests should describe scope, affected documents, validation commands and any unresolved review items; never claim production readiness while sign-off tables remain pending.

## Security & Configuration Tips

Never commit real credentials, tokens, cookies, customer mail, contracts, or personal data. Use `.test` identifiers and redacted examples. Preserve default-deny rules: unapproved or uncertain sends, cross-tenant access, prompt injection, unsafe attachments, and `SEND_UNKNOWN` must remain blocked or routed to human review.

## 项目文档
在对话开始之前，先阅读以下文档，了解项目的总体路线图和介绍，readme.md文件是项目的入口，包含了项目的所有文档的地址方便随时索引：
1. /E:/PIAgent/10-projects/AgentLearn/AI-Operations-Assistant/docs/企业级邮件运营助手-逐Step实施路线图.md (项目总体路线图)
2. /E:/PIAgent/10-projects/AgentLearn/AI-Operations-Assistant/docs/README.md (项目介绍)

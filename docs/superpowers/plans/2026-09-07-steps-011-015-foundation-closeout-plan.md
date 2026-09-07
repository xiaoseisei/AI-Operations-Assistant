# Step 011–015 准备阶段收尾 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 完成质量门禁、本地基础设施检查、领域 Schema、Alembic 迁移基线和可复现 Demo fixture，闭合 Level 0 准备阶段。

**Architecture:** CI 和本地脚本复用同一组 uv 命令。领域模型位于 `src/ai_ops/domain`，数据库实现位于 `src/ai_ops/infrastructure/db`，外部 Provider 仍隔离在 connectors；迁移只依赖数据库模型，Demo 使用 SQLite 与 Mock，不调用 Gmail/飞书/LLM。

**Tech Stack:** Python 3.12、Pydantic v2、SQLAlchemy 2、Alembic、pytest、Ruff、mypy、pip-audit、GitHub Actions、Docker Compose、JSON/EML/Markdown。

**Spec:** 路线图 Step 011–015；用户已确认 2026-09-07 实施方案。

## Global Constraints

- 质量门禁必须覆盖 lint、类型、测试、secret scan、依赖审计和迁移检查。
- Docker 服务使用 PostgreSQL 16、Redis 7、MinIO 固定 digest、持久化卷和独立网络。
- 未知 Schema 字段、缺字段和不可映射事件必须拒绝或隔离。
- 数据库迁移使用 Alembic；禁止手工 SQL 代替版本迁移。
- Demo fixture 只使用 `.test` 标识、合成正文和非敏感附件元数据。

---

### Task 1: Step 011 Quality Gates

Create `.github/workflows/ci.yml`, `scripts/check_secrets.py`, `scripts/check_migrations.py`; add tests for both scripts. CI runs locked sync, Ruff, mypy, pytest, pip-audit, secret scan, and migration check. Scripts must exit nonzero on findings and never print secret values.

### Task 2: Step 012 Infrastructure Checks

Extend `compose.yaml` with an isolated `backend` network and explicit service health checks/volumes. Create `scripts/infra_check.ps1` and `scripts/infra_check.py` to validate Compose config, fixed digests, named volumes, network isolation, and Docker daemon availability. Docker-unavailable mode reports actionable pending status; SQLite remains the offline fallback.

### Task 3: Step 013 Domain Schemas

Create versioned Pydantic models for Tenant, Mailbox, Thread, Message, Draft, Approval, FollowUp, ProfileFact, KnowledgeDocument, AgentRun, and EventEnvelope. Use strict unknown-field rejection, stable provider/internal/thread/event IDs, timestamps, and `schema_version`. Add JSON Schema export and unit tests for valid, missing, unknown, old-version, and quarantined events.

### Task 4: Step 014 Alembic Baseline

Create `alembic.ini`, `alembic/env.py`, `src/ai_ops/infrastructure/db/{base,models,session}.py`, and migration `alembic/versions/0001_initial.py`. Define tables and constraints for the core domain plus send attempts and audit events. Add migration tests for upgrade, idempotent current revision, and SQLite offline compatibility.

### Task 5: Step 015 Demo and Closeout

Create synthetic fixtures under `fixtures/{emails,knowledge,expected}`, `scripts/run_demo.py`, and `docs/demo-runbook.md`. Cover FAQ, address, high risk, multi-intent, empty body, HTML, attachment metadata, injection, timeout, duplicate, and follow-up cancellation. Update README/AGENTS and add `docs/14-Step011-015验收记录.md`; run the complete local gate and record Docker/network limitations honestly.


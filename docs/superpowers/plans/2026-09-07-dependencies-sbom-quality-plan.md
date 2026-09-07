# Step 009 锁定依赖、SBOM 和质量工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 为邮件运营助手锁定 Python 运行时/开发依赖、PostgreSQL/Redis/MinIO 镜像和可重复质量检查，并生成版本化 SBOM。

**Architecture:** 使用 `pyproject.toml` 的生产依赖与 `dev` 依赖分组，`uv.lock` 作为唯一解析结果；运行时层只声明后续骨架需要的框架、领域模型、持久化、队列、LangGraph 和观测接口，质量工具留在开发组。Compose 通过固定镜像 digest-friendly tag 描述本地 PostgreSQL 16、Redis 7 和 MinIO 服务，SBOM 从锁定依赖生成并记录生成工具/时间/版本。

**Tech Stack:** Python 3.12、uv、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、LangGraph 1.x、DeepAgents、OpenTelemetry、psycopg、redis、boto3、pytest、pytest-cov、Ruff、mypy、pip-audit、CycloneDX、Docker Compose v2。

**Spec:** `docs/superpowers/specs/2026-09-04-email-ops-foundation-design.md`；路线图 Step 009。

## Global Constraints

- 使用 `pyproject.toml` + `uv.lock` + SBOM；禁止把 `pip install` 成功当作可复现证据。
- 生产依赖与开发质量工具分组；不提前引入未使用的大型依赖。
- PostgreSQL 固定 16 系列、Redis 固定 7 系列、MinIO 使用固定版本标签；禁止使用 `latest`。
- 干净环境/CI 必须从 `uv.lock` 得到同一依赖图；解析冲突时调整约束并重新锁定。
- 不加入真实凭据；SBOM 和报告不得包含 Token、Cookie 或客户数据。

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | 运行时依赖、dev 依赖、Ruff/pytest/mypy 配置 |
| `uv.lock` | uv 解析后的完整、可复现依赖图 |
| `compose.yaml` | 固定 PostgreSQL/Redis/MinIO 开发镜像与健康检查 |
| `compose.dev.yaml` | 本地 offline healthcheck 覆盖配置 |
| `scripts/generate_sbom.ps1` | Windows SBOM 生成入口 |
| `scripts/generate_sbom.sh` | POSIX SBOM 生成入口 |
| `sbom/cyclonedx-python.json` | 提交的 Python 依赖 SBOM |
| `docs/10-依赖与质量工具基线.md` | 版本、工具、锁定和 CI 使用说明 |
| `docs/11-Step009验收记录.md` | 实际命令、版本、SBOM hash 和遗留项 |
| `docs/README.md` | Step 009 导航和状态 |
| `AGENTS.md` | 依赖、质量和 SBOM 命令说明 |

### Task 1: Lock Runtime and Development Dependencies

**Files:**

- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**

- Consumes: Python 3.12 baseline and current package skeleton.
- Produces: resolved production/dev dependency groups and a reproducible uv lock file.

- [ ] **Step 1: Declare production dependencies**

  Add these production dependencies with bounded major versions: `fastapi>=0.115,<1`, `pydantic>=2.10,<3`, `pydantic-settings>=2.6,<3`, `sqlalchemy>=2.0,<3`, `alembic>=1.14,<2`, `langgraph>=1,<2`, `deepagents>=0.1,<1`, `opentelemetry-api>=1.29,<2`, `opentelemetry-sdk>=1.29,<2`, `psycopg[binary]>=3.2,<4`, `redis>=5,<6`, and `boto3>=1.35,<2`.

  Keep the existing project metadata and `requires-python = ">=3.12,<3.13"`. Do not add Gmail or Feishu SDKs yet; those belong to later connector steps.

- [ ] **Step 2: Declare development quality tools**

  Set the `dev` dependency group to include `pytest>=8,<9`, `pytest-cov>=5,<6`, `ruff>=0.9,<1`, `mypy>=1.14,<2`, `pip-audit>=2.7,<3`, and `cyclonedx-bom>=7,<8`. Keep these out of `[project].dependencies`.

- [ ] **Step 3: Add tool configuration**

  Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["src"]`, and `addopts = "-ra"`; add `[tool.ruff]` with `target-version = "py312"`, `line-length = 100`, and `src = ["src", "tests", "scripts"]`; add `[tool.ruff.lint]` with `select = ["E", "F", "I", "UP", "B"]`; add `[tool.mypy]` with `python_version = "3.12"`, `check_untyped_defs = true`, and `disallow_untyped_defs = true`.

- [ ] **Step 4: Resolve and synchronize the lock file**

  Run:

  ```powershell
  uv lock
  uv sync --dev
  uv run python -c "import fastapi, pydantic, sqlalchemy, alembic, langgraph, opentelemetry, psycopg, redis, boto3; print('runtime imports pass')"
  ```

  Expected: lock resolution succeeds, the dev environment is synchronized, and the import check exits 0. If a package constraint conflicts, adjust only the affected bounded version and rerun `uv lock`; do not remove a required capability to hide the conflict.

- [ ] **Step 5: Run quality tools on the current skeleton**

  ```powershell
  uv run ruff check src tests scripts
  uv run mypy src
  uv run pytest -q
  ```

  Expected: all checks pass; the current skeleton has no business implementation to exempt. Record exact failures if a tool requires a targeted configuration change.

- [ ] **Step 6: Commit dependency and quality configuration**

  ```powershell
  git add -- pyproject.toml uv.lock
  git commit -m 'chore: lock runtime dependencies and quality tools'
  ```

### Task 2: Pin Local Infrastructure Images

**Files:**

- Modify: `compose.yaml`
- Modify: `compose.dev.yaml`

**Interfaces:**

- Consumes: `.env.example` and Step 007 Compose path conventions.
- Produces: PostgreSQL 16, Redis 7 and MinIO fixed-version services with no `latest` tag or real credentials.

- [ ] **Step 1: Add fixed-version infrastructure services**

  Add services `postgres`, `redis`, and `minio` to `compose.yaml` using `postgres:16.4`, `redis:7.4.1`, and `minio/minio:RELEASE.2024-10-13T13-34-11Z`. Use named volumes and container paths `/var/lib/postgresql/data`, `/data`, and `/data`; add healthchecks using the image-local commands. Use safe local defaults only: database `ai_ops`, user `ai_ops`, password `local-only-not-secret`, and MinIO access/secret values explicitly marked development-only.

- [ ] **Step 2: Keep the offline overlay safe**

  Keep `compose.dev.yaml` able to run the healthcheck service without requiring the infrastructure services. It may override `APP_MODE=offline`, but must not replace fixed image tags with `latest`, hard-code a Windows drive path, or add real secrets.

- [ ] **Step 3: Validate normalized Compose configuration**

  ```powershell
  docker compose -f compose.yaml -f compose.dev.yaml config
  if (Select-String -Path compose.yaml,compose.dev.yaml -Pattern '[:/]latest(["'']|$)' -Quiet) { throw 'latest tag is forbidden' }
  @('postgres:16.4','redis:7.4.1','minio/minio:RELEASE.2024-10-13T13-34-11Z') | ForEach-Object { if (-not (Select-String -Path compose.yaml -SimpleMatch $_ -Quiet)) { throw "Missing image $_" } }
  ```

  Expected: Compose config exits 0; all three fixed image tags are present; no `latest` or host drive-letter path appears.

- [ ] **Step 4: Commit infrastructure pinning**

  ```powershell
  git add -- compose.yaml compose.dev.yaml
  git commit -m 'chore: pin local infrastructure image versions'
  ```

### Task 3: Generate and Verify the SBOM

**Files:**

- Create: `scripts/generate_sbom.ps1`
- Create: `scripts/generate_sbom.sh`
- Create: `sbom/.gitkeep`
- Generate: `sbom/cyclonedx-python.json`

**Interfaces:**

- Consumes: `uv.lock` and the `cyclonedx-bom` dev tool.
- Produces: a versioned CycloneDX JSON SBOM whose components match the locked environment.

- [ ] **Step 1: Implement the PowerShell SBOM command**

  The script must create `sbom/`, invoke `uv run --locked --with cyclonedx-bom cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --output-format JSON --output-file sbom/cyclonedx-python.json .venv`, and print `SBOM_GENERATED <path>`. Resolve paths relative to the repository root and fail if the output file is absent or empty. Do not include environment values in the output.

- [ ] **Step 2: Implement the POSIX SBOM command**

  Implement the equivalent script using a script-relative repository root, `mkdir -p sbom`, the same CycloneDX command, and an explicit nonzero failure when the output is absent or empty.

- [ ] **Step 3: Generate the SBOM from the locked environment**

  ```powershell
  pwsh -NoProfile -File scripts/generate_sbom.ps1
  ```

  Expected: `sbom/cyclonedx-python.json` exists, parses as JSON, has `bomFormat = "CycloneDX"`, and contains at least one component with a name and version.

- [ ] **Step 4: Check SBOM reproducibility metadata**

  Verify the SBOM contains the project name/version and compare its component names to `uv.lock` package names. Record the generation command, date, uv version and SHA-256 in the acceptance note. Do not require byte-for-byte equality if the generator emits a timestamp; component/version equality is the reproducibility assertion.

- [ ] **Step 5: Commit the SBOM task**

  ```powershell
  git add -- scripts/generate_sbom.ps1 scripts/generate_sbom.sh sbom/.gitkeep sbom/cyclonedx-python.json
  git commit -m 'chore: add locked dependency SBOM generation'
  ```

### Task 4: Document Quality Gates and Record Acceptance

**Files:**

- Create: `docs/10-依赖与质量工具基线.md`
- Create: `docs/11-Step009验收记录.md`
- Modify: `docs/README.md`
- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: dependency lock, Compose pins, SBOM scripts and tool configuration.
- Produces: documented clean-machine/CI commands and an honest Step 009 review state.

- [ ] **Step 1: Document dependency groups and version policy**

  Describe production versus dev dependencies, Python 3.12, uv lock workflow, bounded versions, no direct Gmail/Feishu SDK at this step, and the rule that CI uses `uv sync --locked --dev` rather than unconstrained installation.

- [ ] **Step 2: Document quality and SBOM commands**

  Include exact commands for `uv lock --check`, `uv sync --locked --dev`, `uv run ruff check src tests scripts`, `uv run mypy src`, `uv run pytest -q`, `uv run pip-audit`, and `pwsh -NoProfile -File scripts/generate_sbom.ps1`. Explain that all failures block the quality gate and that SBOM is regenerated when `uv.lock` changes.

- [ ] **Step 3: Update navigation and contributor instructions**

  Add Step 009 to `docs/README.md` as `DEPENDENCY_REVIEW_REQUIRED` and link `docs/10-依赖与质量工具基线.md`. Update `AGENTS.md` with the new source/tests/scripts/SBOM commands while preserving the no-secrets rule.

- [ ] **Step 4: Write acceptance evidence**

  Record actual dependency/tool versions, `uv lock --check`, locked sync, import, Ruff, mypy, pytest, pip-audit, Compose config, SBOM JSON validation, SBOM SHA-256, and any network/cache limitation. Keep the status `DEPENDENCY_REVIEW_REQUIRED` until human review; do not claim production readiness.

- [ ] **Step 5: Commit documentation and acceptance record**

  ```powershell
  git add -- docs/10-依赖与质量工具基线.md docs/11-Step009验收记录.md docs/README.md AGENTS.md
  git commit -m 'docs: record step 009 dependency quality baseline'
  ```

### Task 5: Run the Full Step 009 Gate

**Files:**

- Verify: all Step 009 files and `uv.lock`

- [ ] **Step 1: Run reproducibility checks**

  ```powershell
  uv lock --check
  uv sync --locked --dev
  uv run python -c "import fastapi, pydantic, sqlalchemy, alembic, langgraph, opentelemetry, psycopg, redis, boto3; print('runtime imports pass')"
  ```

  Expected: no lock drift, clean locked sync and successful imports.

- [ ] **Step 2: Run quality checks**

  ```powershell
  uv run ruff check src tests scripts
  uv run mypy src
  uv run pytest -q
  uv run pip-audit
  ```

  Expected: all commands pass or documented advisories are reviewed; an unresolved vulnerability is not silently ignored.

- [ ] **Step 3: Run infrastructure and SBOM checks**

  ```powershell
  docker compose -f compose.yaml -f compose.dev.yaml config
  pwsh -NoProfile -File scripts/generate_sbom.ps1
  ```

  Expected: Compose renders, SBOM parses and component versions match the locked dependency graph.

- [ ] **Step 4: Run hygiene and scope checks**

  ```powershell
  git diff --check -- .
  git status --short
  git ls-files .env .runtime '*.sqlite3' '.venv/*'
  ```

  Expected: no whitespace errors; no secrets/local state tracked; only intended Step 009 files are changed.

- [ ] **Step 5: Commit any final acceptance-only correction**

  If the acceptance note needs an actual version/hash correction, commit only that note with `docs: correct step 009 acceptance evidence`; otherwise leave the verified commit history unchanged.

## Execution Notes

- Run tasks in order because the lock file feeds SBOM generation and the final acceptance record.
- Use `apply_patch` for source/config/document edits and exact `git add --` paths.
- Network access may be needed once to resolve packages; after `uv.lock` is generated, CI must use locked/offline-compatible installation where possible.
- The initial images use fixed version tags, not digests; production should promote digest pinning before external deployment.

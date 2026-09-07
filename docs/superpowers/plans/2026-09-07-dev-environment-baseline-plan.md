# Step 007 固定开发环境 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 固化 Python、uv、Node.js、Docker Compose 和 Windows/Linux 路径规则，并提供可在 Docker 不可用时运行的 SQLite + Mock 离线健康检查。

**Architecture:** 采用配置优先、宿主机与容器边界清晰的环境基线。Python 项目元数据由 `pyproject.toml` 和 `.python-version` 声明，uv 负责锁定依赖；Docker Compose 只描述后续服务的本地运行接口，离线健康检查不依赖 Docker 或外部服务。所有敏感配置只在 `.env.example` 中声明变量名，实际 `.env` 永不提交。

**Tech Stack:** Python 3.12、uv、Node.js 20 LTS、Docker Engine 24+、Docker Compose v2、PowerShell 7+/Windows PowerShell、POSIX shell、SQLite、Mock Adapter。

**Spec:** `docs/superpowers/specs/2026-09-04-email-ops-foundation-design.md`（Step 007 方案由用户确认于 2026-09-07）

## Global Constraints

- Python 固定为 3.12.x；依赖管理使用 `uv`。
- Node.js 固定为 20 LTS；Docker Engine 要求 24+；Docker Compose 要求 v2。
- 容器内部统一使用 POSIX 路径 `/app/...`；Windows 主机路径通过相对路径或环境变量传入，不写死盘符。
- Docker 不可用时必须能使用 SQLite + Mock 模式完成最小健康检查；生产 Gate 仍需要容器验证。
- `.env`、Token、Cookie、API Key、OAuth 凭据和本地数据库文件不得提交。
- 当前仓库无业务运行时代码，本 Step 只建立环境骨架，不实现 Gmail、飞书或 LLM 连接器。

---

## File Map

| File | Responsibility |
|---|---|
| `.python-version` | 声明 Python 3.12 解释器系列 |
| `pyproject.toml` | Python 项目元数据、最低 Python 版本和工具入口 |
| `.env.example` | 脱敏环境变量模板 |
| `.gitignore` | 忽略虚拟环境、缓存、`.env`、SQLite 和构建产物 |
| `compose.yaml` | Docker Compose v2 的最小开发服务占位与 POSIX 路径约定 |
| `scripts/healthcheck.ps1` | Windows/PowerShell 环境健康检查与离线降级 |
| `scripts/healthcheck.sh` | Linux/macOS POSIX 环境健康检查与离线降级 |
| `docs/06-开发环境基线.md` | 安装、版本、路径、离线模式、验证和故障处理说明 |
| `docs/README.md` | 增加 Step 007 文档入口与状态 |
| `AGENTS.md` | 更新仓库结构、命令和环境基线说明 |

### Task 1: Add Version and Secret Boundaries

**Files:**

- Create: `.python-version`
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`

**Interfaces:**

- Produces: Python 3.12 and uv-readable project metadata; safe configuration names; ignored local state.

- [ ] **Step 1: Declare Python and project metadata**

  Write `.python-version` with exactly `3.12`. Write `pyproject.toml` with a PEP 621 project named `ai-operations-assistant`, version `0.1.0`, `requires-python = ">=3.12,<3.13"`, no runtime dependencies yet, and a `healthcheck` script entry pointing to `scripts/healthcheck.ps1` for documentation only.

- [ ] **Step 2: Add the environment template**

  Write `.env.example` containing only variable names and safe defaults:

  ```dotenv
  APP_ENV=local
  APP_MODE=offline
  SQLITE_PATH=.runtime/app.sqlite3
  COMPOSE_PROJECT_NAME=ai-operations-assistant
  ```

  Add comments stating that real credentials belong in a secret manager or local untracked `.env`, never in this file.

- [ ] **Step 3: Add ignore rules**

  Write `.gitignore` covering `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.env`, `.env.*` except `.env.example`, `.runtime/`, `*.sqlite3`, `*.sqlite3-journal`, `dist/`, `build/`, `node_modules/`, Docker override files, and OS/editor files.

- [ ] **Step 4: Verify the boundary files**

  Run:

  ```powershell
  if ((Get-Content -Raw .python-version).Trim() -ne '3.12') { throw 'Python version must be 3.12' }
  rg -n 'requires-python|name =|version =' pyproject.toml
  rg -n 'TOKEN|SECRET|KEY|PASSWORD|OAUTH' .env.example
  git check-ignore .env .runtime/app.sqlite3 node_modules .venv
  ```

  Expected: Python metadata is present, `.env.example` contains names only, and all local-state paths are ignored.

- [ ] **Step 5: Commit the version-boundary task**

  ```powershell
  git add -- .python-version pyproject.toml .env.example .gitignore
  git commit -m 'chore: fix development version and secret boundaries'
  ```

### Task 2: Add Cross-Platform Health Checks

**Files:**

- Create: `scripts/healthcheck.ps1`
- Create: `scripts/healthcheck.sh`
- Create: `scripts/healthcheck-fixture.json`

**Interfaces:**

- Consumes: `.python-version`, `.env.example`, local toolchain commands.
- Produces: exit code 0 for a valid local toolchain or explicit SQLite+Mock offline mode; nonzero only for invalid Python/uv or malformed fixture.

- [ ] **Step 1: Define the health fixture**

  Write `scripts/healthcheck-fixture.json` with a fake tenant `tenant-demo-a`, fake thread `thread-demo-health`, mode `offline`, and `database = sqlite`. It must contain no real address, token, cookie or customer content.

- [ ] **Step 2: Implement the PowerShell check**

  Implement `scripts/healthcheck.ps1` with `param([switch]$RequireDocker)`. It must check that `python --version` is 3.12.x, `uv --version` is callable, and the fixture parses as JSON. In default mode, Docker and Node are reported as `WARN` when unavailable but do not fail the command; `-RequireDocker` makes missing Docker/Compose fail. Print a final `HEALTHCHECK_PASS mode=offline database=sqlite adapter=mock` line on success.

- [ ] **Step 3: Implement the POSIX check**

  Implement `scripts/healthcheck.sh` with `--require-docker` support and equivalent checks using `python`, `uv`, `node`, `docker`, and `docker compose`. Resolve the fixture using a script-relative path so it works from any current directory. Use `/app/...` only for container examples, never for host filesystem resolution.

- [ ] **Step 4: Verify offline behavior**

  Run on Windows:

  ```powershell
  pwsh -NoProfile -File scripts/healthcheck.ps1
  ```

  Expected: exit code 0 with `mode=offline`, even if Docker is unavailable; missing Python 3.12 or uv must be clearly reported and exit nonzero.

- [ ] **Step 5: Verify strict container behavior**

  Run:

  ```powershell
  pwsh -NoProfile -File scripts/healthcheck.ps1 -RequireDocker
  ```

  Expected: exit code 0 only when Docker and `docker compose version` are available; otherwise exit nonzero with an actionable message. Do not install software automatically from the health check.

- [ ] **Step 6: Commit the health-check task**

  ```powershell
  git add -- scripts/healthcheck.ps1 scripts/healthcheck.sh scripts/healthcheck-fixture.json
  git commit -m 'chore: add offline development health checks'
  ```

### Task 3: Add the Docker Compose Development Boundary

**Files:**

- Create: `compose.yaml`
- Create: `compose.dev.yaml`

**Interfaces:**

- Consumes: `.env.example` variable names and health-check mode.
- Produces: Docker Compose v2 syntax with POSIX container paths and no required external credentials.

- [ ] **Step 1: Define the base Compose file**

  Write `compose.yaml` with a `healthcheck` service placeholder using a local build context and `/app` workdir, plus a named volume for `/app/.runtime`. Do not reference a host drive letter, real image registry, secret value, Gmail credential, or production endpoint. The service command must run the offline health check fixture path.

- [ ] **Step 2: Define the development override**

  Write `compose.dev.yaml` with a `healthcheck` service override, `APP_MODE=offline`, `SQLITE_PATH=/app/.runtime/app.sqlite3`, and a relative bind mount for the repository. Keep all container paths POSIX and make the override optional so host-only development remains possible.

- [ ] **Step 3: Validate Compose syntax**

  Run:

  ```powershell
  docker compose -f compose.yaml -f compose.dev.yaml config
  ```

  Expected: normalized YAML with no Windows drive-letter paths and no unresolved secret values. If Docker is unavailable, run a static path/placeholder check and record the limitation in the environment guide.

- [ ] **Step 4: Commit the Compose task**

  ```powershell
  git add -- compose.yaml compose.dev.yaml
  git commit -m 'chore: define container development boundary'
  ```

### Task 4: Document the Development Environment

**Files:**

- Create: `docs/06-开发环境基线.md`
- Modify: `docs/README.md`
- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: all environment files and health-check commands from Tasks 1–3.
- Produces: a clean-machine setup guide targeting installation within approximately 10 minutes and an honest distinction between offline local mode and production container verification.

- [ ] **Step 1: Write the environment matrix**

  Document Python 3.12.x, uv, Node.js 20 LTS, Docker Engine 24+, Docker Compose v2, Windows PowerShell and POSIX shell requirements. Include a table with “required locally”, “optional for offline mode”, and “required for production Gate”.

- [ ] **Step 2: Document Windows/Linux path rules**

  State that Windows commands may use repository-relative paths or `Join-Path`, Linux/macOS commands use POSIX paths, and containers always use `/app/...`. Show one safe example for each platform and explicitly forbid hard-coded `E:\...` or `/home/...` paths in committed Compose/config files.

- [ ] **Step 3: Document setup and fallback commands**

  Include:

  ```text
  uv python install 3.12
  uv sync
  pwsh -NoProfile -File scripts/healthcheck.ps1
  docker compose -f compose.yaml -f compose.dev.yaml config
  ```

  Explain that SQLite + Mock is the offline fallback when Docker is unavailable, while production Gate requires Compose validation. Include a troubleshooting table for missing Python, missing uv, missing Node, missing Docker, path mount failures and malformed `.env`.

- [ ] **Step 4: Update navigation and contributor instructions**

  Add a Step 007 row and link to `docs/README.md`. Update `AGENTS.md` so its structure and commands describe the new files while retaining the no-secrets rule and future runtime-test caveat.

- [ ] **Step 5: Verify documentation references**

  Run:

  ```powershell
  @('Python 3.12','uv','Node.js 20','Docker Compose','SQLite','Mock','/app/','E:\\') |
    ForEach-Object { if (-not (Select-String -Path docs/06-开发环境基线.md -SimpleMatch $_ -Quiet)) { throw "Missing environment term: $_" } }
  Select-String -Path docs/README.md -SimpleMatch '06-开发环境基线.md'
  ```

  Expected: all environment terms and the Step 007 link are present; the committed config examples contain no real credentials.

- [ ] **Step 6: Commit the documentation task**

  ```powershell
  git add -- docs/06-开发环境基线.md docs/README.md AGENTS.md
  git commit -m 'docs: document fixed development environment'
  ```

### Task 5: Run the Full Step 007 Acceptance Check

**Files:**

- Verify: `.python-version`, `pyproject.toml`, `.env.example`, `.gitignore`, `compose.yaml`, `compose.dev.yaml`, `scripts/*`, `docs/06-开发环境基线.md`, `docs/README.md`, `AGENTS.md`

- [ ] **Step 1: Run repository hygiene checks**

  ```powershell
  git diff --check -- .
  $targets = Get-ChildItem -Path . -Recurse -File -Include '*.md','*.toml','*.yaml','*.yml','*.env.example','*.ps1','*.sh','*.json' |
    Where-Object { $_.FullName -notlike '*\\docs\\superpowers\\*' }
  $matches = rg -n 'BEGIN (RSA|OPENSSH|PRIVATE)|ghp_[A-Za-z0-9]|xox[baprs]-|AIza[0-9A-Za-z_-]{20,}|-----BEGIN|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.' -- $targets 2>&1
  if ($LASTEXITCODE -eq 0) { Write-Output $matches; throw 'Credential-like content found' }
  ```

  Expected: no whitespace errors and no credential-like matches.

- [ ] **Step 2: Run host-only offline verification**

  Run the PowerShell health check and verify it exits 0 with the SQLite + Mock line. If the local machine does not have Python 3.12 or uv, report the exact missing prerequisite; do not silently downgrade the declared version.

- [ ] **Step 3: Run strict environment verification**

  Run the Compose config check and `healthcheck.ps1 -RequireDocker` when Docker is available. Record whether Docker was available; “offline health check passed” must not be reported as “production container Gate passed”.

- [ ] **Step 4: Verify tracked scope**

  ```powershell
  git status --short
  git diff --cached --check
  git ls-files
  ```

  Expected: only intended Step 007 files are staged/committed; `.env`, `.runtime`, virtual environments and generated caches are not tracked.

- [ ] **Step 5: Commit the acceptance record**

  If a separate verification note is needed, create `docs/07-Step007验收记录.md` with command outputs, date, tool versions, offline/container result and unresolved prerequisites. Do not mark production readiness unless Docker Compose verification actually passed.

  ```powershell
  git add -- docs/07-Step007验收记录.md
  git commit -m 'docs: record step 007 environment verification'
  ```

## Execution Notes

- Run tasks in order; Task 2 depends on the version and fixture conventions from Task 1, and Task 4 documents the final paths from Tasks 1–3.
- Use `apply_patch` for file edits and exact `git add --` paths.
- Do not install dependencies automatically as part of a health check. Installation is an explicit developer action using the documented commands.
- If Docker is unavailable, complete the offline check and record strict Compose verification as pending; this is an environment limitation, not permission to change the production target.

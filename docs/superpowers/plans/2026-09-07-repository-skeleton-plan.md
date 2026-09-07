# Step 008 创建仓库骨架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 建立 `src/ai_ops` 分层包、测试/部署目录和骨架检查，使 Gmail/LLM 实现可替换且不会散落到 Graph 节点。

**Architecture:** 采用依赖方向由外向内的 Python 包结构。`domain` 只保存领域接口/模型，`application` 编排用例，`graphs`/`agents` 负责状态编排，`connectors`/`infrastructure` 实现外部适配；`api` 和脚本位于最外层。Step 008 只创建包入口、接口占位、测试夹具和结构检查，不接入真实供应商或数据库。

**Tech Stack:** Python 3.12、uv、pytest（测试目录约定）、PowerShell、POSIX shell、Markdown。

**Spec:** `docs/superpowers/specs/2026-09-04-email-ops-foundation-design.md`；路线图 Step 008。

## Global Constraints

- 建立 `src/ai_ops/{api,domain,graphs,agents,skills,tools,connectors,knowledge,memory,application,infrastructure}`、`tests/`、`deploy/`、`scripts/`、`docs/`。
- 领域层、应用层、适配器层、基础设施层分离；依赖方向由外向内。
- Gmail SDK 调用不得散落在 Graph 节点，必须由 `EmailProvider` Adapter 隔离。
- 替换 Gmail/LLM 实现不需要修改领域模型；循环依赖时缩小模块边界。
- 不实现 Gmail、飞书、LLM、数据库或业务流程；不增加真实凭据和供应商依赖。

---

## File Map

| File/Directory | Responsibility |
|---|---|
| `src/ai_ops/*/__init__.py` | 明确 Python 包边界，保持模块可导入 |
| `src/ai_ops/domain/interfaces.py` | 定义 `EmailProvider` 和 `LLMProvider` 最小协议 |
| `src/ai_ops/connectors/README.md` | 说明真实/Mock Adapter 隔离规则 |
| `tests/fixtures/README.md` | 说明脱敏 fixture 规范 |
| `scripts/check_skeleton.py` | 检查必需目录、包入口、接口和禁止依赖文本 |
| `deploy/.gitkeep` | 保留部署配置目录 |
| `docs/08-仓库骨架说明.md` | 记录模块职责、依赖方向和替换策略 |
| `docs/README.md` | 增加 Step 008 入口和状态 |
| `AGENTS.md` | 更新代码/测试/骨架命令和目录说明 |

### Task 1: Create the Layered Package Skeleton

**Files:**

- Create: `src/ai_ops/{api,domain,graphs,agents,skills,tools,connectors,knowledge,memory,application,infrastructure}/__init__.py`
- Create: `tests/{unit,integration,contract,fixtures}/.gitkeep`
- Create: `deploy/.gitkeep`

**Interfaces:**

- Produces: Importable `ai_ops` package and stable layer directories; no implementation side effects.

- [ ] **Step 1: Create package directories and entries**

  Create the eleven directories under `src/ai_ops` and place an empty `__init__.py` in each. Add a package-level `src/ai_ops/__init__.py` containing only `__version__ = "0.1.0"`. Keep the entries free of imports so the skeleton cannot create cycles.

- [ ] **Step 2: Create test, fixture, and deployment directories**

  Create `tests/unit`, `tests/integration`, `tests/contract`, `tests/fixtures`, and `deploy`; add `.gitkeep` only where Git would otherwise omit an empty directory. Do not create sample customer data or credentials.

- [ ] **Step 3: Verify package imports**

  Run:

  ```powershell
  $env:PYTHONPATH = (Join-Path (Resolve-Path '.') 'src')
  python -c "import ai_ops; import ai_ops.domain; import ai_ops.graphs; import ai_ops.connectors; print(ai_ops.__version__)"
  ```

  Expected: prints `0.1.0` and exits 0.

- [ ] **Step 4: Commit the package skeleton**

  ```powershell
  git add -- src tests deploy
  git commit -m 'chore: create layered application skeleton'
  ```

### Task 2: Define Replaceable Provider Interfaces

**Files:**

- Create: `src/ai_ops/domain/interfaces.py`
- Create: `src/ai_ops/connectors/README.md`
- Create: `tests/contract/test_provider_interfaces.py`

**Interfaces:**

- Produces: `EmailProvider` and `LLMProvider` Protocols that outer layers can consume without importing SDKs.

- [ ] **Step 1: Write the contract test**

  Create a test that defines local fake implementations and asserts they satisfy the expected callable shape without importing Gmail, Feishu, OpenAI or other provider SDKs:

  ```python
  from ai_ops.domain.interfaces import EmailProvider, LLMProvider

  class FakeEmailProvider:
      def fetch_message(self, message_id: str) -> dict:
          return {"message_id": message_id}

  class FakeLLMProvider:
      def generate(self, prompt: str) -> str:
          return prompt

  def test_provider_interfaces_are_provider_neutral():
      email: EmailProvider = FakeEmailProvider()
      llm: LLMProvider = FakeLLMProvider()
      assert email.fetch_message("msg-demo") == {"message_id": "msg-demo"}
      assert llm.generate("prompt-demo") == "prompt-demo"
  ```

- [ ] **Step 2: Run the contract test before implementation**

  ```powershell
  $env:PYTHONPATH = (Join-Path (Resolve-Path '.') 'src')
  python -m pytest tests/contract/test_provider_interfaces.py -q
  ```

  Expected: FAIL because `ai_ops.domain.interfaces` does not yet exist.

- [ ] **Step 3: Implement provider-neutral Protocols**

  Write `src/ai_ops/domain/interfaces.py` using `typing.Protocol`:

  ```python
  from typing import Protocol

  class EmailProvider(Protocol):
      def fetch_message(self, message_id: str) -> dict: ...

  class LLMProvider(Protocol):
      def generate(self, prompt: str) -> str: ...
  ```

  Do not import a provider SDK or add implementation logic.

- [ ] **Step 4: Add the adapter boundary guide**

  Document that Gmail/Feishu/LLM SDK calls belong under `connectors/`, Graph nodes consume `domain.interfaces`, and Mock/Real implementations must share contract tests. State that a provider replacement must not modify `domain/interfaces.py`.

- [ ] **Step 5: Run the contract test after implementation**

  ```powershell
  $env:PYTHONPATH = (Join-Path (Resolve-Path '.') 'src')
  python -m pytest tests/contract/test_provider_interfaces.py -q
  ```

  Expected: PASS.

- [ ] **Step 6: Commit the interface task**

  ```powershell
  git add -- src/ai_ops/domain/interfaces.py src/ai_ops/connectors/README.md tests/contract/test_provider_interfaces.py
  git commit -m 'feat: define provider-neutral adapter contracts'
  ```

### Task 3: Add Skeleton Documentation and Static Boundary Check

**Files:**

- Create: `scripts/check_skeleton.py`
- Create: `tests/fixtures/README.md`
- Create: `docs/08-仓库骨架说明.md`
- Modify: `docs/README.md`
- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: package directories and provider interfaces from Tasks 1–2.
- Produces: repeatable `python scripts/check_skeleton.py` check with exit 0 for a valid skeleton.

- [ ] **Step 1: Write the static checker test expectations**

  The checker must verify the eleven package directories, four test directories, `deploy`, all package `__init__.py` files, `src/ai_ops/domain/interfaces.py`, and `tests/contract/test_provider_interfaces.py`. It must scan Python files under `src/ai_ops` and fail if they contain imports of `googleapiclient`, `openai`, `langchain`, `langgraph`, `feishu`, or `imaplib` in this skeleton step.

- [ ] **Step 2: Implement the static checker**

  Implement `scripts/check_skeleton.py` using `pathlib`, `ast`, and `sys`. Resolve the repository root from `Path(__file__).resolve().parents[1]`; print one `PASS` line per check and exit 1 with the relative path and reason for any failure. The successful final line must be `SKELETON_CHECK_PASS`.

- [ ] **Step 3: Write the skeleton guide**

  Document every layer’s single responsibility, the allowed dependency direction, the `EmailProvider` boundary, the test directory meanings, and explicit non-goals. Include a Mermaid dependency diagram and examples for `PYTHONPATH`/`uv run` invocation.

- [ ] **Step 4: Update project navigation and contributor guide**

  Add a Step 008 row to `docs/README.md` with status `SKELETON_REVIEW_REQUIRED` and link `docs/08-仓库骨架说明.md`. Update `AGENTS.md` to list `src/ai_ops`, `tests`, `deploy`, the checker command, and the fact that provider implementations are not present yet.

- [ ] **Step 5: Run the skeleton check**

  ```powershell
  python scripts/check_skeleton.py
  ```

  Expected: exit 0 with `SKELETON_CHECK_PASS`.

- [ ] **Step 6: Commit the boundary-check task**

  ```powershell
  git add -- scripts/check_skeleton.py tests/fixtures/README.md docs/08-仓库骨架说明.md docs/README.md AGENTS.md
  git commit -m 'docs: document and verify repository skeleton'
  ```

### Task 4: Run Step 008 Acceptance and Record Evidence

**Files:**

- Create: `docs/09-Step008验收记录.md`

- [ ] **Step 1: Run package and contract checks**

  ```powershell
  $env:PYTHONPATH = (Join-Path (Resolve-Path '.') 'src')
  python -c "import ai_ops; print(ai_ops.__version__)"
  python -m pytest tests/contract/test_provider_interfaces.py -q
  python scripts/check_skeleton.py
  ```

  Expected: all commands exit 0.

- [ ] **Step 2: Run repository hygiene checks**

  ```powershell
  git diff --check -- .
  rg -n 'BEGIN (RSA|OPENSSH|PRIVATE)|ghp_[A-Za-z0-9]|xox[baprs]-|AIza[0-9A-Za-z_-]{20,}|-----BEGIN|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.' --glob '!docs/superpowers/**' .
  ```

  Expected: no whitespace errors and no credential-like matches. If the plan text itself contains the regex, limit the scan to committed runtime/config/docs files outside `docs/superpowers`.

- [ ] **Step 3: Write the acceptance record**

  Record actual tool versions, package import result, contract test result, skeleton checker result, Docker-independent scope, and unresolved review status. Do not claim Gmail/LLM/database implementation or production readiness.

- [ ] **Step 4: Commit the acceptance record**

  ```powershell
  git add -- docs/09-Step008验收记录.md
  git commit -m 'docs: record step 008 skeleton acceptance'
  ```

## Execution Notes

- Run tasks in order. The provider contract test intentionally starts as a failing test before the interface is added.
- Use `apply_patch` for file edits and exact `git add --` paths.
- Do not run dependency installation or create real provider credentials. Existing `uv.lock` remains valid because the skeleton adds no runtime dependency.
- If Python 3.12 is unavailable, use the project’s documented `py -3.12` launcher path and record the actual command in the acceptance note.

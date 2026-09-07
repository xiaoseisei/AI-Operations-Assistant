# 企业级邮件运营助手 Step 1–5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 将企业级 AI 邮件运营助手 Level 0 的 Step 001–005 落地为可评审、可签字、可追踪和可复核的项目基线文档，不提前实现运行时代码。

**Architecture:** 采用文档优先的治理基线。README 负责入口和状态，五份主题文档分别负责范围、任务风险、UAT、架构 ADR、数据分类与威胁模型；跨文档通过稳定的 Step 编号、任务 ID、UAT ID、ADR ID 和威胁 ID 关联。文档约束后续应用层的路由、权限、证据、审批、外发和故障终态。

**Tech Stack:** Markdown、Mermaid、Git、PowerShell 静态文档检查。

**Spec:** `docs/superpowers/specs/2026-09-04-email-ops-foundation-design.md`

## Global Constraints

- 一期能力围绕 Gmail 邮件回复、飞书审批、知识库检索、自动跟进和最小客户画像。
- 一期所有外发邮件默认必须经过人工审批；任何自动直发能力均属于后续经过单独评审的变更。
- 业务风险规则和不可逆动作门禁由确定性服务/策略实现，模型只能提供分类、抽取和草稿建议，不能单独放行风险动作。
- 每个任务都必须有预期路由、允许工具、禁止动作和终态；没有定义的任务进入人工处理或安全终态。
- 文档中的真实凭据、客户原文、合同全文、Token、Cookie 和密钥一律不写入；示例使用伪造标识。
- 项目采用每客户独立 Docker Compose 的早期部署假设，多租户平台化属于后续演进；文档仍必须明确租户隔离边界。
- 本批次不创建应用代码、FastAPI 路由、数据库迁移、Docker Compose、真实 OAuth、真实 Gmail/飞书调用、LangGraph Checkpoint、LLM Prompt、生产密钥、SBOM、CI 或独立 Git 仓库。

---

## File Map

| File | Responsibility | Produced by |
|---|---|---|
| `docs/README.md` | 文档入口、Step 状态、评审责任人和验收索引 | Task 1 |
| `docs/01-一期范围冻结.md` | 一期 In/Out、延期项、变更规则和三方签字 | Task 1 |
| `docs/02-成功任务与风险矩阵.md` | 任务契约、P0/P1/P2、路由、工具白名单和终态 | Task 2 |
| `docs/03-用户旅程与UAT场景.md` | Mermaid 时序图、20 个主流程和 20 个异常流程 | Task 3 |
| `docs/04-架构决策记录.md` | ADR-001–008 及替代方案、风险、回滚/迁移 | Task 4 |
| `docs/05-数据分类与威胁模型.md` | 四级数据分类、数据流、T-001–012 和 Break-glass | Task 5 |

---

### Task 1: Freeze the First-Release Scope

**Files:**

- Create: `docs/README.md`
- Create: `docs/01-一期范围冻结.md`
- Reference: `docs/superpowers/specs/2026-09-04-email-ops-foundation-design.md`

**Interfaces:**

- Consumes: 设计规格第 3 节的范围表、明确不做项和范围冻结规则。
- Produces: README 中稳定的五份文档链接；范围文档中的 `in_scope`、`out_of_scope`、`deferred` 三组边界，以及 `SCOPE_REVIEW_REQUIRED` 初始状态。

- [ ] **Step 1: Create the documentation index**

  Write `docs/README.md` with the title, project purpose, links to the roadmap and full specification, and this exact status table shape:

  ```markdown
  | Step | 文档 | 当前状态 | 责任人 | 验收证据 |
  |---:|---|---|---|---|
  | 001 | [一期范围冻结](01-一期范围冻结.md) | SCOPE_REVIEW_REQUIRED | 业务/技术/交付 | 三方签字栏 |
  | 002 | [成功任务与风险矩阵](02-成功任务与风险矩阵.md) | TASK_REVIEW_REQUIRED | 业务/技术/安全 | 任务契约完整 |
  | 003 | [用户旅程与 UAT 场景](03-用户旅程与UAT场景.md) | UAT_REVIEW_REQUIRED | 业务/交付/QA | 20+20 场景 |
  | 004 | [架构决策记录](04-架构决策记录.md) | ADR_REVIEW_REQUIRED | 技术/安全/运维 | ADR-001–008 |
  | 005 | [数据分类与威胁模型](05-数据分类与威胁模型.md) | SECURITY_REVIEW_REQUIRED | 安全/技术/运维 | 四级分类 + STRIDE |
  ```

  Add a note that these statuses are review states, not implementation or production approval, and link the five documents with relative links.

- [ ] **Step 2: Write the scope table and non-goals**

  Write `docs/01-一期范围冻结.md` with these required sections in order: `状态与责任人`, `一期目标`, `In Scope`, `明确不做`, `二期候选与变更规则`, `一期硬边界`, `签字与遗留事项`.

  The `In Scope` table must contain exactly these capability rows: Gmail 入站与标准化、回复草稿、知识库检索、飞书审批发送、自动跟进、最小客户画像、审计与安全；each row must state a user-visible result and evidence. The non-goal table must contain CRM/ERP、Slack/企微/Microsoft 365、批量营销、合同/价格/退款自动动作、无审批直发、跨客户画像共享、开放式 Shell/浏览器工具、生产多租户平台化 and unreviewed attachment execution.

  Explicitly state that real integrations are later steps while the Level 1 demo may use Mock Adapters, that all outbound mail is manual approval by default, and that a customer request outside the scope becomes a `PROPOSED` change request without changing the一期 Gate.

- [ ] **Step 3: Add the three-party sign-off record**

  Add a sign-off table with columns `角色`, `姓名`, `结论`, `签字/日期`, `遗留事项`, and rows `业务负责人`, `技术负责人`, `交付/QA 负责人`. Set the initial conclusion to `待评审`; do not fabricate names or signatures.

- [ ] **Step 4: Run the Step 001 documentation check**

  Run:

  ```powershell
  $f = 'docs/01-一期范围冻结.md'
  @('In Scope','明确不做','二期候选与变更规则','一期硬边界','业务负责人','技术负责人','交付/QA 负责人','SCOPE_REVIEW_REQUIRED') |
    ForEach-Object { if (-not (Select-String -Path $f -SimpleMatch $_ -Quiet)) { throw "Missing Step 001 requirement: $_" } }
  ```

  Expected: the command exits successfully and prints no missing requirement.

- [ ] **Step 5: Commit the self-contained scope deliverable**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/README.md' '10-projects/AgentLearn/AI-Operations-Assistant/docs/01-一期范围冻结.md'
  git commit -m 'docs: freeze email assistant first-release scope'
  ```

### Task 2: Define Successful Tasks and the Risk Matrix

**Files:**

- Create: `docs/02-成功任务与风险矩阵.md`
- Modify: `docs/README.md` only if the link or status text needs correction

**Interfaces:**

- Consumes: `docs/01-一期范围冻结.md` and the Step 002 requirements in the design specification.
- Produces: stable task IDs `TASK-001` through `TASK-015`, risk labels `P0/P1/P2`, explicit route/tool/terminal columns, and the invariant that deterministic rules override model risk signals.

- [ ] **Step 1: Define the task contract and priority rules**

  Add a task-contract section with these required fields: `task_id`, `输入特征`, `成功定义`, `拒答/转人工条件`, `风险等级`, `预期路由`, `允许工具`, `禁止动作`, `证据要求`, `终态`, `失败行为`.

  Define `P0` as a possible security, compliance, wrong commercial commitment, duplicate-send or irreversible-side-effect incident; `P1` as material impact or uncertainty requiring approval; and `P2` as a bounded routine request. State that the highest deterministic risk wins over model classification and that no task without a defined contract may send.

- [ ] **Step 2: Add the 15 required task rows**

  Add one complete row for each stable task ID below, without collapsing distinct scenarios into a generic “other” row:

  | ID | Task |
  |---|---|
  | TASK-001 | 普通 FAQ |
  | TASK-002 | 产品/技术咨询 |
  | TASK-003 | 复杂异议 |
  | TASK-004 | 投诉 |
  | TASK-005 | 退订 |
  | TASK-006 | 退款/合同 |
  | TASK-007 | 报价/折扣 |
  | TASK-008 | 会议安排 |
  | TASK-009 | 跟进触发 |
  | TASK-010 | 恶意 Prompt Injection |
  | TASK-011 | 越权读取/跨租户请求 |
  | TASK-012 | 恶意或不可解析附件 |
  | TASK-013 | 身份不明/权限不足 |
  | TASK-014 | 重复事件 |
  | TASK-015 | 供应商超时/发送结果不确定 |

  For routine FAQ and technical requests, allow only scoped knowledge read and draft generation, ending at `PENDING_APPROVAL`. For complaints, unsubscribe, refund/contract, pricing, injection, unauthorized access and unsafe attachments, define the correct human, suppression or quarantine path and explicitly forbid external side effects. For `TASK-015`, require `SEND_UNKNOWN` and prohibit blind resend when the provider result is uncertain.

- [ ] **Step 3: Add deterministic outbound invariants**

  Write a “不可绕过规则” section containing these exact invariants:

  ```text
  没有匹配的 APPROVED 记录、草稿 hash、权限、证据和当前策略版本，Adapter 不得发送。
  退订、投诉、暂停、越权、证据不足和版本冲突不得进入自动外发路径。
  SEND_UNKNOWN 只能进入补偿查询或人工队列，不能通过普通重试发送。
  ```

- [ ] **Step 4: Check every task row**

  Run:

  ```powershell
  $f = 'docs/02-成功任务与风险矩阵.md'
  1..15 | ForEach-Object { $id = 'TASK-{0:D3}' -f $_; if (-not (Select-String -Path $f -SimpleMatch $id -Quiet)) { throw "Missing $id" } }
  @('P0','P1','P2','预期路由','允许工具','禁止动作','终态','证据要求','SEND_UNKNOWN','模型分类') |
    ForEach-Object { if (-not (Select-String -Path $f -SimpleMatch $_ -Quiet)) { throw "Missing Step 002 term: $_" } }
  ```

  Expected: all 15 IDs and all contract/risk terms are found.

- [ ] **Step 5: Commit the task-contract deliverable**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/02-成功任务与风险矩阵.md'
  git commit -m 'docs: define email task contracts and risk matrix'
  ```

### Task 3: Write the User Journey and 40 UAT Scenarios

**Files:**

- Create: `docs/03-用户旅程与UAT场景.md`
- Modify: `docs/README.md` only if the link or status text needs correction

**Interfaces:**

- Consumes: Task 1 scope, Task 2 task IDs/risk rules, and the Step 003 journey requirements.
- Produces: a Mermaid end-to-end sequence and stable UAT IDs `UAT-H-001..020` and `UAT-E-001..020`; every scenario has Given/When/Then plus state and evidence assertions.

- [ ] **Step 1: Add the journey overview and Mermaid sequence**

  Start the document with `状态与责任人`, `验收原则`, and a Mermaid `sequenceDiagram` with these participants: Gmail, Inbound/Inbox, Workflow, Knowledge/Profile, 飞书审批, Outbox/Send Adapter, Scheduler and Audit. The sequence must show inbound normalization/deduplication, Thread/Run start, knowledge/profile read, triage, draft, approval, version check, idempotent send, follow-up registration and inbound invalidation.

  State that HTTP 200 alone is never UAT evidence; external side effects require business state, audit event and Adapter evidence, while blocked actions require a queryable block/security event.

- [ ] **Step 2: Write the 20 happy-path scenarios**

  Use one heading per ID and the exact scenario inventory below:

  | IDs | Scenario |
  |---|---|
  | UAT-H-001 | 新邮件入站并标准化 |
  | UAT-H-002 | 同一事件去重 |
  | UAT-H-003 | 正常 FAQ 生成草稿 |
  | UAT-H-004 | 知识证据被引用 |
  | UAT-H-005 | 产品技术问题回复 |
  | UAT-H-006 | 复杂异议进入增强路径 |
  | UAT-H-007 | 画像快照只读加载 |
  | UAT-H-008 | 人工编辑草稿 |
  | UAT-H-009 | 飞书审批通过 |
  | UAT-H-010 | 飞书审批拒绝 |
  | UAT-H-011 | 飞书审批转人工 |
  | UAT-H-012 | 版本匹配后创建发送请求 |
  | UAT-H-013 | Mock Gmail 发送成功 |
  | UAT-H-014 | 发送结果写入审计 |
  | UAT-H-015 | 跟进计划成功注册 |
  | UAT-H-016 | 客户新邮件取消跟进 |
  | UAT-H-017 | 有证据的画像候选生成 |
  | UAT-H-018 | 多轮 Thread 上下文延续 |
  | UAT-H-019 | 业务人员查看完整处理轨迹 |
  | UAT-H-020 | 普通任务安全完成并归档 |

- [ ] **Step 3: Write the 20 exception scenarios**

  Use one heading per ID and the exact scenario inventory below:

  | IDs | Scenario |
  |---|---|
  | UAT-E-001 | 重复入站事件 |
  | UAT-E-002 | 知识库无命中 |
  | UAT-E-003 | 证据不足或事实冲突 |
  | UAT-E-004 | 合同或退款要求 |
  | UAT-E-005 | 投诉邮件 |
  | UAT-E-006 | 退订邮件 |
  | UAT-E-007 | 邮件中的 Prompt Injection |
  | UAT-E-008 | 跨租户读取请求 |
  | UAT-E-009 | 恶意附件 |
  | UAT-E-010 | 不可解析附件 |
  | UAT-E-011 | Gmail 权限撤销 |
  | UAT-E-012 | 飞书回调重复或重放 |
  | UAT-E-013 | 草稿版本冲突 |
  | UAT-E-014 | 租户或 Thread 被暂停 |
  | UAT-E-015 | Gmail 发送超时 |
  | UAT-E-016 | 发送结果为 SEND_UNKNOWN |
  | UAT-E-017 | 瞬态故障重试达到上限 |
  | UAT-E-018 | DLQ 人工处理 |
  | UAT-E-019 | 数据脱敏命中高危字段 |
  | UAT-E-020 | 数据库/Redis 不可用 |

- [ ] **Step 4: Apply the Given/When/Then evidence template**

  Every scenario must use this structure, with concrete values such as `tenant-demo-a`, `thread-demo-001` and `run-demo-001` only:

  ```gherkin
  场景: <scenario name>
  Given <tenant/thread/run, version, permission and dependency state>
  When <one user or system action>
  Then <observable business result>
  And <Graph/database/Outbox state>
  And <audit event, Adapter evidence or security event>
  ```

  Do not use real addresses, contracts, credentials, customer names or opaque claims. For every exception scenario explicitly state the safe terminal state and why no unauthorized external side effect occurred.

- [ ] **Step 5: Verify the 40-scenario inventory**

  Run:

  ```powershell
  $f = 'docs/03-用户旅程与UAT场景.md'
  $happy = (Select-String -Path $f -Pattern '^### UAT-H-\d{3}' | Measure-Object).Count
  $exception = (Select-String -Path $f -Pattern '^### UAT-E-\d{3}' | Measure-Object).Count
  if ($happy -lt 20 -or $exception -lt 20) { throw "Expected at least 20 happy and 20 exception scenarios; got $happy/$exception" }
  @('Given','When','Then','数据库','审计','Adapter','sequenceDiagram','SEND_UNKNOWN') |
    ForEach-Object { if (-not (Select-String -Path $f -SimpleMatch $_ -Quiet)) { throw "Missing UAT evidence term: $_" } }
  ```

  Expected: counts are at least `20/20` and all evidence terms are found.

- [ ] **Step 6: Commit the UAT deliverable**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/03-用户旅程与UAT场景.md'
  git commit -m 'docs: add email assistant user journeys and UAT cases'
  ```

### Task 4: Record the Architecture Decisions

**Files:**

- Create: `docs/04-架构决策记录.md`
- Modify: `docs/README.md` only if the link or status text needs correction

**Interfaces:**

- Consumes: the scope, task contracts, UAT evidence requirements and Step 004 design section.
- Produces: ADR-001–008 with a consistent decision schema and explicit rollback/migration behavior for later implementation tasks.

- [ ] **Step 1: Define the ADR template**

  Add a template section requiring these fields in every ADR: `Status`, `Context`, `Decision`, `Alternatives`, `Consequences`, `Costs`, `Risks`, `Rollback/Migration`, and `Acceptance Evidence`. Use `Proposed — pending architecture/security/operations review` for the initial status; do not claim production acceptance.

- [ ] **Step 2: Write ADR-001 through ADR-004**

  Create decisions for: `FastAPI 控制面`, `LangGraph 外层业务状态机`, `DeepAgent 作为 CompiledStateGraph 子图`, and `Worker/Queue 异步执行`. For each, explain why synchronous API-only execution, a free-form agent, a remote-only subagent and in-request long-running work were rejected; state the operational cost, failure risk, pause/recovery behavior and migration condition.

- [ ] **Step 3: Write ADR-005 through ADR-008**

  Create decisions for: `PostgreSQL/Redis/MinIO 分工`, `Gmail/飞书/LLM Adapter 隔离`, `不可逆动作确定性最终门禁`, and `数据最小化与脱敏默认开启`. Each ADR must name the data or side-effect boundary it controls, the alternative that was rejected, and the evidence required before it can be implemented or promoted.

- [ ] **Step 4: Add the cross-component boundary and migration rules**

  State explicitly: Inbound only receives/normalizes; Workflow owns state transitions and routing; Knowledge/Profile provides scoped reads; approval UI carries decisions but not business truth; Outbox/Adapter owns idempotent side effects; Audit stores immutable events. State that workflow, task contract, Adapter and database Schema versions are separate, and that rollback pauses outbound, preserves evidence and uses a compatible previous version or human queue.

- [ ] **Step 5: Verify all ADR fields and IDs**

  Run:

  ```powershell
  $f = 'docs/04-架构决策记录.md'
  1..8 | ForEach-Object { $id = 'ADR-{0:D3}' -f $_; if (-not (Select-String -Path $f -SimpleMatch $id -Quiet)) { throw "Missing $id" } }
  @('Status','Context','Decision','Alternatives','Consequences','Costs','Risks','Rollback/Migration','Acceptance Evidence','确定性最终门禁','MinIO') |
    ForEach-Object { if (-not (Select-String -Path $f -SimpleMatch $_ -Quiet)) { throw "Missing ADR term: $_" } }
  ```

  Expected: all eight IDs and all ADR fields are present.

- [ ] **Step 6: Commit the ADR deliverable**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/04-架构决策记录.md'
  git commit -m 'docs: record email assistant architecture decisions'
  ```

### Task 5: Classify Data and Model Threats

**Files:**

- Create: `docs/05-数据分类与威胁模型.md`
- Modify: `docs/README.md` only if the link or status text needs correction

**Interfaces:**

- Consumes: scope, task risk rules, UAT evidence, ADR boundaries and Step 005 design section.
- Produces: Public/Internal/Confidential/Restricted policy table, Mermaid data-flow diagram, threats `T-001..012`, and auditable Break-glass rules.

- [ ] **Step 1: Write the four-level data policy**

  Add a table with exactly four levels: `Public`, `Internal`, `Confidential`, `Restricted`. Each row must define examples, storage, access scope, retention, logging treatment and LLM/Prompt treatment. Restricted examples must include OAuth refresh tokens, API keys, signing keys and contract/payment/identity materials; state that they use Docker secrets or a KMS-compatible secret store and never enter ordinary logs, metrics labels or prompts.

- [ ] **Step 2: Add the data-flow diagram and boundaries**

  Add a Mermaid `flowchart LR` showing Gmail → Inbound Adapter → normalization/deduplication → PostgreSQL and MinIO; Workflow → Knowledge/Profile Reader → draft/security gate → Feishu approval → Outbox → Gmail Send Adapter; Worker/Scheduler and redacted Audit/Trace must also be shown. Mark raw MIME/attachments/snapshots as Blob references and state that all reads are tenant- and Thread-scoped.

- [ ] **Step 3: Add the 12 STRIDE threats**

  Add one row for each ID below with asset/boundary, threat, control, owner or verification evidence, and safe terminal state:

  `T-001` fake/replayed Gmail event; `T-002` cross-tenant or cross-Thread read; `T-003` Prompt Injection; `T-004` long-term memory poisoning; `T-005` unapproved/expired outbound; `T-006` timeout duplicate send; `T-007` follow-up collision; `T-008` malicious attachment/SSRF; `T-009` PII/contract/token leakage in logs; `T-010` stolen or overbroad OAuth/KMS permissions; `T-011` poison message/infinite retry/resource exhaustion; `T-012` supply-chain or insecure deployment.

- [ ] **Step 4: Add Break-glass and default-deny rules**

  Require an incident/ticket ID, reason, approver, minimum fields, tenant scope, start/end time and export audit for every Break-glass access. State that unknown classification, permission, tenant, version or send status defaults to read-only/manual handling. Include a data-minimization rule for Prompt, Trace, Checkpoint, Outbox and snapshot inputs.

- [ ] **Step 5: Verify classification and threat coverage**

  Run:

  ```powershell
  $f = 'docs/05-数据分类与威胁模型.md'
  @('Public','Internal','Confidential','Restricted','flowchart LR','STRIDE','Break-glass','Docker secrets','KMS','脱敏','租户','Thread') |
    ForEach-Object { if (-not (Select-String -Path $f -SimpleMatch $_ -Quiet)) { throw "Missing security term: $_" } }
  1..12 | ForEach-Object { $id = 'T-{0:D3}' -f $_; if (-not (Select-String -Path $f -SimpleMatch $id -Quiet)) { throw "Missing $id" } }
  ```

  Expected: all four classifications, the data-flow diagram, all 12 threats and the Break-glass policy are found.

- [ ] **Step 6: Commit the threat-model deliverable**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/05-数据分类与威胁模型.md'
  git commit -m 'docs: define email assistant data classification and threats'
  ```

### Task 6: Cross-Link, Scan, and Close the Step 1–5 Baseline

**Files:**

- Modify: `docs/README.md`
- Verify: `docs/01-一期范围冻结.md`
- Verify: `docs/02-成功任务与风险矩阵.md`
- Verify: `docs/03-用户旅程与UAT场景.md`
- Verify: `docs/04-架构决策记录.md`
- Verify: `docs/05-数据分类与威胁模型.md`

**Interfaces:**

- Consumes: all five completed topic documents.
- Produces: a reproducible static verification result and a README that reports review states honestly.

- [ ] **Step 1: Check all relative links**

  Run:

  ```powershell
  $root = 'docs'
  $required = @('README.md','01-一期范围冻结.md','02-成功任务与风险矩阵.md','03-用户旅程与UAT场景.md','04-架构决策记录.md','05-数据分类与威胁模型.md')
  foreach ($name in $required) { if (-not (Test-Path (Join-Path $root $name))) { throw "Missing $name" } }
  foreach ($name in $required[1..5]) { if (-not (Select-String -Path 'docs/README.md' -SimpleMatch $name -Quiet)) { throw "README does not link $name" } }
  ```

  Expected: all six files exist and README links to all five topic documents.

- [ ] **Step 2: Scan for forbidden secret-like content**

  Run:

  ```powershell
  $targets = Get-ChildItem -Path docs -File -Filter '*.md' | Select-Object -ExpandProperty FullName
  $matches = rg -n 'BEGIN (RSA|OPENSSH|PRIVATE)|ghp_[A-Za-z0-9]|xox[baprs]-|AIza[0-9A-Za-z_-]{20,}|-----BEGIN|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.' -- $targets 2>&1
  if ($LASTEXITCODE -eq 0) { Write-Output $matches; throw 'Forbidden credential-like content found' }
  ```

  Expected: no output. Mentions of “Token” or “API key” are policy terms only and must not be followed by a credential value.

- [ ] **Step 3: Run the complete document acceptance check**

  Re-run the checks from Tasks 1–5, then inspect only the current project directory. Do not assume a fixed number of commits because the project lives below a shared parent repository:

  ```powershell
  git diff --check -- '10-projects/AgentLearn/AI-Operations-Assistant/docs'
  git diff --cached --check -- '10-projects/AgentLearn/AI-Operations-Assistant/docs'
  git status --short -- '10-projects/AgentLearn/AI-Operations-Assistant/docs'
  ```

  Expected: no whitespace errors and no unexpected project files. If the shared parent repository has unrelated modifications, they remain outside the exact project path and absent from the task commits.

- [ ] **Step 4: Set honest review status and report evidence**

  Keep Step 001–005 statuses as review-required until the business, technology, delivery/QA and security owners sign the relevant tables. Do not change the status to “已完成”, “生产就绪” or “已验收” based solely on static Markdown checks.

- [ ] **Step 5: Commit the cross-link and verification update**

  ```powershell
  git add -- '10-projects/AgentLearn/AI-Operations-Assistant/docs/README.md'
  git commit -m 'docs: index and verify email assistant foundation baseline'
  ```

## Execution Notes

- Run each task in order because later documents consume stable IDs and boundaries from earlier tasks.
- Use `apply_patch` for content edits. Use `git add -- <exact project paths>` so unrelated files in `E:\PIAgent` cannot enter a commit.
- This plan has no runtime test suite because the approved scope is documentation-only. The PowerShell checks above are the required static acceptance evidence; later implementation steps must add contract, integration, security and end-to-end tests.
- If a reviewer disputes scope, risk, architecture or data handling, keep the affected document in its review-required state and record the issue in its `遗留事项` table rather than silently changing the一期 boundary.

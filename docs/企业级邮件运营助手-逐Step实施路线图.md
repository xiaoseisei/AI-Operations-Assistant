# 企业级 AI 邮件运营助手：0→1→100 逐 Step 实施路线图

> 文档性质：可执行的项目建设、评测、上线和运营基线
> 目标用户：自动化服务商、自由职业者和企业 AI 工程团队
> 首期产品：Gmail 邮件回复、飞书审批、知识库检索、自动跟进、最小客户画像
> 部署形态：每客户独立 Docker Compose；后续可演进为多租户平台
> 默认安全策略：所有外发邮件均需人工审批
> 版本：v1.0 路线图草案

---

## 0. 先把“0、1、100”定义清楚

这不是“写三步”的计划，而是 **100 个可追踪、可验收、可回退的 Step**。Step 编号是执行顺序；Level 是成熟度里程碑。

| Level | 对应 Step | 含义 | 必须达到的结果 |
|---|---:|---|---|
| 0 | 001–015 | 项目开始前准备 | 环境、仓库、骨架、契约、数据和 Demo 运行条件就绪 |
| 1 | 016–035 | 可运行 Demo | 模拟 Gmail 入站→知识检索→回复草稿→审批→模拟外发，失败和审计也能演示 |
| 10 | 036–045 | 持久化底座 | PostgreSQL、Checkpoint、Store、Blob、Inbox/Outbox、队列可恢复 |
| 20 | 046–055 | 真实外部接入 | Gmail OAuth/PubSub 和飞书回调在 staging 安全运行 |
| 30 | 056–065 | Agent 生产化 | 外层 LangGraph + 内嵌 DeepAgent、工具权限、复杂度路由和循环熔断 |
| 40 | 066–075 | 知识、附件、画像和安全 | 版本化知识、证据门禁、附件、国际化、Prompt Injection 和画像一致性 |
| 50 | 076–083 | 审批、发送和跟进 | 飞书审批、幂等发送、发送不确定补偿、跟进零撞车、暂停开关 |
| 60 | 084–089 | 异常、权限、可靠性 | 错误分类、重试、DLQ、RBAC、OAuth 轮换、安全测试 |
| 70 | 090–094 | 可观测、成本、容量和高可用 | Trace、指标、成本账本、限流、扩缩容和容灾基础 |
| 80 | 095–097 | 版本、灾备和运营 | 迁移、回滚、备份恢复、事故 Runbook 和值班体系 |
| 90 | 098–099 | 评测、影子和灰度 | Golden Dataset、离线回放、A/B、影子流量和发布门禁 |
| 100 | 100 | 企业级交付完成 | 可运营、可审计、可回放、可优化、可回滚，并通过正式验收 |

重要声明：文档中的 `T` 表示目标门槛，`M` 表示需要通过测试或生产数据实测的结果。当前项目尚未上线，因此不能把任何 `M` 写成既成事实。

---

## 1. 固定架构和边界

```text
Gmail / Google Pub/Sub / 飞书
              ↓ HTTPS
          FastAPI 控制面
   验签 · 鉴权 · 幂等 · 查询 · 控制
              ↓ Inbox / Outbox / Queue
          LangGraph Worker
       外层业务状态和生命周期
              ↓
       Reply DeepAgent 子图
   规划 · Skills · 只读 Tools · 合成
              ↓
     事实校验 → 飞书审批 → 发送守卫
              ↓
 PostgreSQL | Redis | pgvector | MinIO/S3
```

职责边界：

- FastAPI 不运行长时间 LLM 任务，只接收外部事件、验证、幂等、入队、查询和控制。
- LangGraph 管理业务状态、Checkpoint、interrupt/resume、重试和生命周期。
- DeepAgent 只处理复杂邮件的规划和工具编排，不能直接发 Gmail、写正式画像、改配置或执行 Shell。
- PostgreSQL 是业务事实源；Redis 是队列、锁和限流协调器，不是唯一状态源。
- MinIO/S3 保存原始 EML、附件、快照和大文本；Graph 状态只保存引用和小型结构化字段。
- 所有外发、跟进、审批和画像正式写入都由确定性应用服务最终裁决。

首期不做：无审批直发、CRM 深度同步、营销自动化、项目管理集成、客户独立微调、Kubernetes 平台化、任意 Shell 和任意 SQL。

---

## 2. 统一评测指标和门禁

### 2.1 关键公式

```text
PassRate              = 通过任务数 / 总任务数
Intent-F1             = 意图分类 Macro F1
Stage-F1              = 销售阶段 Macro F1
Recall@K              = 召回相关文档数 / 相关文档总数
CitationPrecision     = 真正支持声明的引用数 / 全部引用数
UnsupportedClaimRate  = 无证据声明数 / 全部商业声明数
RouterAccuracy        = 选择正确执行路径的任务数 / 总任务数
LoopRate              = 发生无进展循环的运行数 / Agent 运行数
RecoveryRate          = 从故障恢复并完成的任务数 / 可恢复故障任务数
CostPerSuccess        = 总模型及基础设施成本 / 成功业务任务数
AcceptanceRate        = 未修改直接采用草稿数 / 总审批任务数
```

### 2.2 首期硬门槛（不是已实测成绩）

```text
未经审批外发                 = 0
跟进撞车                     = 0
跨租户读取成功               = 0
高风险无证据声明外发         = 0
重复事件重复副作用           = 0
发送结果不确定时盲目重试     = 0
关键状态丢失                 = 0
P0 安全违规攻击成功率        = 0
```

建议质量目标，需用真实数据校准：RAG Recall@5 ≥ 0.85、引用准确率 ≥ 0.95、核心任务通过率 ≥ 0.85、路由准确率 ≥ 0.90、工具参数正确率 ≥ 0.98、无效循环率 < 0.02。性能、成本和转化类指标必须在固定负载与真实试点后报告 P50/P95/P99 和置信区间。

### 2.3 指标不达标的统一优化原则

```text
指标异常
  → 定位到路由 / Prompt / Skill / Tool / 知识 / 状态 / 连接器
  → 固定一个变量做实验
  → Golden Dataset + 时间留出集 + 安全集回归
  → 影子流量
  → 小比例灰度
  → 观察窗口
  → 保留或回滚
```

不允许用一次 Prompt 修改解决所有问题；不允许在没有基线时声称“提升了 20%”。

---

# Part I：Level 0——项目开始前准备（Step 001–015）

## Step 001：冻结一期业务范围

- 做什么：把“邮件回复、审批发送、自动跟进、最小画像”写成范围表，同时列出明确不做项。
- 选型：Markdown 规格文档、版本化 ADR；不把自由文本需求直接当实现任务。
- 场景拷问：客户临时要求 CRM 同步或自动直发时，是扩范围还是记录为二期？答案必须是记录为后续能力，不改变一期 Gate。
- 验收/失败：业务、技术、交付三方签字后冻结；有争议就停在本 Step，不进入编码。

## Step 002：定义成功任务和风险矩阵

- 做什么：定义普通 FAQ、复杂异议、投诉、退订、退款/合同、恶意注入等任务的成功、拒答和转人工条件。
- 选型：`P0/P1/P2` 风险等级 + 任务契约；安全规则由代码实现，模型只提供信号。
- 场景拷问：模型说“低风险”，但邮件要求修改合同，是否放行？不放行，风险规则优先。
- 验收/失败：每个场景都有预期路由、允许工具和终态；缺失定义时回到业务评审。

## Step 003：编写用户旅程和 UAT 场景

- 做什么：画出 Gmail 入站、回复草稿、飞书审批、发送、跟进取消、画像更新和异常处理的时序图。
- 选型：Mermaid + 场景表 + Given/When/Then；至少准备 20 个主流程和 20 个异常流程。
- 场景拷问：只看到 API 返回 200，如何证明邮件已检索、已审批、未重复发送？必须有数据库状态、审计事件和外发 Adapter 证据。
- 验收/失败：业务人员可以按场景表判断结果；否则不允许用“Demo 已完成”描述。

## Step 004：固化架构决策记录

- 做什么：记录“FastAPI 控制面 + LangGraph 外层图 + DeepAgent 子图 + Worker + PostgreSQL/Redis/MinIO”的理由、替代方案和升级条件。
- 选型：ADR；DeepAgent 作为内嵌 `CompiledStateGraph`，远程 Async SubAgent 作为未来扩展。
- 场景拷问：为什么不让 DeepAgent 直接接收 HTTP 和发信？因为不可逆动作必须由确定性主图控制。
- 验收/失败：每个关键选型都有成本、风险、回滚和迁移说明；未写清时暂停骨架设计。

## Step 005：建立数据分类和威胁模型

- 做什么：分类 Public、Internal、Confidential、Restricted；识别 OAuth、PII、附件、Prompt Injection、越权、重复外发和供应链风险。
- 选型：STRIDE/数据流图；密钥使用 Docker secrets 或 KMS 兼容方案。
- 场景拷问：工程师排错时是否能从日志还原客户合同？默认不能；需要限时 break-glass 并审计。
- 验收/失败：每类数据有存储、访问、保留和脱敏策略；没有策略的字段禁止进入日志和 LLM Prompt。

## Step 006：建立独立 Git 仓库

- 做什么：在当前项目目录初始化独立 Git，创建 `main`、开发分支、提交规范和版本标签策略。
- 选型：Git、Conventional Commits、`codex/` 分支前缀；不复制上层仓库历史。
- 场景拷问：`.env` 从工作区删除后，历史提交是否仍泄露？是，因此需要 secret scan 和密钥轮换。
- 验收/失败：新仓库有干净初始提交；误提交密钥时立即废弃密钥并重写历史，不能只删文件。

## Step 007：固定开发环境

- 做什么：固定 Python、包管理器、Node/Docker 版本和 Windows/Linux 路径规则。
- 选型：Python 3.12、`uv`、Docker Compose；容器内部统一 POSIX 路径。
- 场景拷问：现场 Docker 不可用，是否仍能演示？Level 0 应提供 SQLite + Mock 的离线模式；生产 Gate 仍需容器验证。
- 验收/失败：干净机器能在约 10 分钟内安装并运行最小健康检查；失败时先降低本地依赖，不改变生产目标。

## Step 008：创建仓库骨架

- 做什么：建立 `src/ai_ops/{api,domain,graphs,agents,skills,tools,connectors,knowledge,memory,application,infrastructure}`、`tests/`、`deploy/`、`scripts/`、`docs/`。
- 选型：领域层、应用层、适配器层、基础设施层分离；依赖方向由外向内。
- 场景拷问：Gmail SDK 调用是否会散落在 Graph 节点？不允许，必须由 `EmailProvider` Adapter 隔离。
- 验收/失败：替换 Gmail/LLM 实现不需要改领域模型；出现循环依赖时缩小模块边界。

## Step 009：锁定依赖、SBOM 和质量工具

- 做什么：添加 FastAPI、Pydantic、SQLAlchemy、Alembic、LangGraph、DeepAgent、pytest、Ruff、OpenTelemetry 等依赖。
- 选型：`pyproject.toml` + `uv.lock` + SBOM；PostgreSQL 16、Redis 7、MinIO 镜像固定版本。
- 场景拷问：`pip install` 成功是否证明可复现？不证明，必须用锁文件和 CI 重装验证。
- 验收/失败：干净环境和 CI 得到同一依赖图；冲突时回退版本，不提前引入未使用的大型依赖。

## Step 010：建立配置和密钥边界

- 做什么：区分代码默认值、环境变量、租户配置、运行时策略和 Restricted Secret。
- 选型：Pydantic Settings；`.env.example` 只含占位符；默认 `AUTO_SEND=false`、Adapter=Mock。
- 场景拷问：字符串 `"false"` 被当成真值怎么办？用强类型解析和启动自检拒绝歧义配置。
- 验收/失败：没有真实密钥也能离线 Demo；生产密钥缺失时服务拒绝启动，而不是降级到错误账户。

## Step 011：建立代码质量和 CI 门禁

- 做什么：配置格式化、Lint、类型检查、单元测试、敏感文件扫描、依赖漏洞扫描和迁移检查。
- 选型：Ruff、pytest、mypy（可逐步启用）、GitHub Actions 或等价 CI。
- 场景拷问：CI 只跑 lint 算不算通过？不算，必须覆盖业务状态和失败路径。
- 验收/失败：合并请求在测试失败、secret scan 命中或迁移不可重复时阻断；失败结果保留为回归样例。

## Step 012：启动本地基础设施

- 做什么：用 Docker Compose 提供 PostgreSQL、Redis、MinIO；SQLite + 本地目录作为无 Docker Demo 备选。
- 选型：PostgreSQL + pgvector、Redis Streams、MinIO S3 API。
- 场景拷问：容器重启后邮件和知识是否消失？卷必须持久化，且要做重启测试。
- 验收/失败：`docker compose up -d`、健康检查、数据卷和网络隔离均通过；容器失败时不能静默改用生产凭据。

## Step 013：定义领域模型和事件 Schema

- 做什么：定义 `Tenant、Mailbox、Thread、Message、Draft、Approval、FollowUp、ProfileFact、KnowledgeDocument、AgentRun`。
- 选型：Pydantic v2 + 版本化 JSON Schema；未来跨语言/高吞吐再评估 Protobuf。
- 场景拷问：同一邮件被 Pub/Sub 投递 5 次、被转发和被回复时，哪些 ID 代表同一业务对象？必须区分 provider ID、thread ID、内部 ID 和事件 ID。
- 验收/失败：未知字段、缺字段、旧版本事件都有明确兼容策略；无法映射的事件进入隔离队列。

## Step 014：建立数据库迁移基线

- 做什么：创建初始表、索引、唯一约束、状态字段、时间字段和审计字段。
- 选型：SQLAlchemy 2 + Alembic；Demo 可 SQLite，生产目标 PostgreSQL。
- 场景拷问：数据库显示 `SENT` 但 Gmail 未发送怎么办？发送状态必须由 `send_attempts` 和外部确认共同决定。
- 验收/失败：迁移可重复执行、可回滚到上一个安全版本；禁止用手工 SQL 替代迁移。

## Step 015：建立 Demo Fixture 和运行手册

- 做什么：准备普通 FAQ、地址查询、高风险请求、多意图、空正文、HTML、附件和恶意提示样例。
- 选型：JSON/EML fixture、Markdown 知识库、Mock LLM 响应；所有数据合成或脱敏。
- 场景拷问：Demo 依赖你电脑上的残留数据库是否算可运行？不算，必须从空数据目录重建。
- 验收/失败：`docs/demo-runbook.md` 能指导新开发者执行；fixture 不足时补边界样例再进入 Level 1。

---

# Part II：Level 1——可运行 Demo（Step 016–035）

## Step 016：实现 Mock Gmail 入站 Adapter

- 做什么：从 fixture 读取邮件，提供 `list/fetch/mark_read` 接口，保存原始内容。
- 选型：`EmailProvider` Protocol + `MockGmailProvider`；返回统一 `InboundMessage`。
- 场景拷问：脚本说“处理 1 封”时，数据库、raw 文件和审计是否都有证据？三者缺一不可。
- 验收/失败：一条命令将邮件落库为 `RECEIVED`；落库失败时不返回业务成功。

## Step 017：实现 MIME、HTML 和纯文本标准化

- 做什么：解析 From/To/Subject/Message-ID/Thread-ID、纯文本、HTML 清洗和附件元数据。
- 选型：Python email parser、HTML sanitizer；正文和附件正文外置保存。
- 场景拷问：HTML 中包含“忽略系统指令”的文本，是否进入 System Prompt？不进入，只作为不可信数据。
- 验收/失败：空正文、编码错误、多部分 MIME 均有明确结果；解析失败转人工而非伪造正文。

## Step 018：实现 Demo Inbox 幂等

- 做什么：以 `tenant_id + provider + provider_message_id` 建立唯一约束，重复事件只返回已处理结果。
- 选型：数据库唯一索引优先，内存集合不作为幂等依据。
- 场景拷问：同一通知重试 3 次是否触发 3 次 Agent？只能产生一个业务事件和一个活动任务。
- 验收/失败：并发重复插入测试 100% 通过；冲突记录保留事件日志，不吞掉真实错误。

## Step 019：建立原始邮件文件存储

- 做什么：将 EML、清洗后的 HTML、附件元数据写入本地 `data/raw`，数据库保存 URI、哈希和大小。
- 选型：Demo 本地 FileStore；生产在 Step 040 切换 S3 兼容 BlobStore。
- 场景拷问：服务重启或数据库只恢复了一半时能否定位原文？通过 content hash 和 URI 校验。
- 验收/失败：文件写入失败阻止事件进入 Agent；孤儿文件进入清理任务而不直接删除。

## Step 020：实现知识文件加载器

- 做什么：扫描本地 Markdown/TXT，记录文件哈希、路径、标题、语言和更新时间。
- 选型：纯 Python loader；PDF/DOCX 留到 Step 066。
- 场景拷问：文件被修改但时间戳未变怎么办？以 content hash 判断版本。
- 验收/失败：重复导入不重复生成文档；解析错误进入 staging 错误报告。

## Step 021：实现结构化分片和来源绑定

- 做什么：按标题、段落和语义边界切块，保存 `document_id/chunk_id/source_path/content_hash`。
- 选型：Demo 先用规则分片；生产再增加表格、价格和有效期元数据。
- 场景拷问：价格限制条件被切到下一块，模型会不会漏读？分片必须保持条件与数值的局部完整性。
- 验收/失败：每个 chunk 可反查原文件和行号；不完整分片回到规则调整，不靠 Prompt 补救。

## Step 022：实现 Demo 检索器

- 做什么：根据问题返回 Top-K chunk、分数和来源；空知识库明确返回 `NO_EVIDENCE`。
- 选型：Demo 可 SQLite FTS/关键词；生产目标 pgvector + 混合检索。
- 场景拷问：没有命中文档时是否仍生成确定性价格？不生成，走拒答或人工。
- 验收/失败：三个固定问题分别命中预期文档；无答案用例必须正确 abstain。

## Step 023：建立 LLM Provider 抽象

- 做什么：定义统一 `classify/generate/structured_output` 接口，实现 Mock 和真实 Provider 两套实现。
- 选型：Pydantic structured output；真实模型通过配置选择，模型无权改变工具权限。
- 场景拷问：Mock 永远成功，如何测试 429、超时和非法 JSON？通过可编程故障注入 Provider。
- 验收/失败：无 API Key 可生成固定草稿；非法输出必须被拒绝或重试，不能静默解析成错误对象。

## Step 024：实现 Triage 和风险分类

- 做什么：分类 `FAQ、REQUEST_ACTION、COMPLAINT、UNSUBSCRIBE、AUTO_REPLY、UNKNOWN` 与风险等级。
- 选型：规则预筛 + 结构化 LLM 分类；代码策略覆盖模型结果。
- 场景拷问：邮件写“请把订单改到明天”，即使包含产品名，也不能当 FAQ。
- 验收/失败：高风险和退订用例 100% 不进入普通外发路径；低置信度转人工。

## Step 025：建立最小 LangGraph 状态图

- 做什么：连接 `ingest→classify→retrieve→draft→safety_check→approval_gate→outbound`，状态只保存小字段和引用。
- 选型：LangGraph `StateGraph`；Demo 可内存 Checkpoint，生产在 Step 038 切换 PostgresSaver。
- 场景拷问：进程在 draft 后崩溃怎么办？必须能看到中间状态并重跑而不重复外发。
- 验收/失败：每个节点有成功、失败和错误原因；不可达节点和无条件发送边全部删掉。

## Step 026：实现普通回复节点

- 做什么：对单意图低风险邮件读取检索结果，输出结构化 `DraftReply`。
- 选型：低成本模型/Mock + 固定模板；输出含 subject、body、claims、evidence_refs、risk_flags。
- 场景拷问：客户问地址但知识库只有旧地址，是否照答？版本无效时必须 abstain 或人工确认。
- 验收/失败：FAQ 可生成草稿且引用证据；证据为空不生成确定性商业事实。

## Step 027：实现第一版事实校验

- 做什么：检查每个商业声明是否有引用，引用是否属于当前检索结果，敏感字段是否符合规则。
- 选型：确定性 Python 断言 + 字符串/span 检查；NLI 以后作为增强，不替代规则。
- 场景拷问：模型把“建议”写成“承诺”怎么办？声明类型和风险级别不同，承诺必须拦截。
- 验收/失败：人为删除引用时测试失败；失败状态为 `BLOCKED_FACT_CHECK` 并进入人工队列。

## Step 028：实现 Demo 审批状态机

- 做什么：创建 `PENDING_APPROVAL/APPROVED/EDITED/REJECTED/EXPIRED` 状态和合法转换。
- 选型：数据库状态机 + 显式命令；不允许前端直接调用发送函数。
- 场景拷问：有人直接 POST `/send` 怎么办？发送服务再次查询审批状态，未审批立即拒绝。
- 验收/失败：无审批事件时外发 Adapter 调用次数为 0；重复 approve 幂等。

## Step 029：实现 Mock 飞书审批 Adapter

- 做什么：把审批卡片写入本地文件/事件表，提供 approve/edit/reject/reassign 模拟回调。
- 选型：`ApprovalChannel` Protocol + MockFeishuChannel；真实飞书留到 Step 052。
- 场景拷问：审批回调重复或乱序怎么办？事件 ID 和版本校验，冲突进入人工复核。
- 验收/失败：审批事件可通过 API 恢复 Graph；Mock 不访问外部网络。

## Step 030：实现 Mock Gmail 外发 Adapter

- 做什么：把最终批准内容写入 outbox 文件，返回模拟 message ID，并记录 draft hash。
- 选型：`EmailSender` Protocol + 本地 Outbox；明确区分 queued/submitted/sent。
- 场景拷问：写入文件是否等于送达？不等于，只能标记模拟 submitted；真实 Provider 需外部确认。
- 验收/失败：批准后才有 outbox 记录；模拟失败时状态为 `SEND_FAILED` 而不是 `SENT`。

## Step 031：暴露最小 FastAPI API

- 做什么：实现健康检查、Mock 入站、运行 Graph、查询消息/草稿/审批/审计、审批决策和知识重建。
- 选型：FastAPI + Pydantic response schema + OpenAPI；路由只调用 application service。
- 场景拷问：API 返回 200 是否代表业务完成？长任务返回 `202 queued`，状态以查询接口为准。
- 验收/失败：不打开数据库，仅通过 API 可完成 Demo；错误有稳定 error code。

## Step 032：加入 Request ID、Trace 和审计

- 做什么：生成 `request_id/trace_id/run_id`，记录节点事件、审批人、草稿 hash 和外发结果。
- 选型：结构化 JSON 日志 + SQLite/DB audit；正文默认只保存引用和掩码。
- 场景拷问：数据库 APPROVED 但没有审计事件是否允许发信？不允许，进入安全阻断。
- 验收/失败：能从 message ID 追到完整执行路径；缺关键事件时 Gate 不通过。

## Step 033：注入 Demo 级故障

- 做什么：模拟 LLM 超时/非法 JSON、知识库为空、数据库异常、审批重复、外发失败和重复入站。
- 选型：pytest monkeypatch/故障注入 Adapter；不依赖真实外部服务。
- 场景拷问：发送接口返回 500 后重跑会不会发两次？应先查幂等记录；Demo 阶段至少证明 Adapter 不重复写 outbox。
- 验收/失败：每个故障有明确状态、错误码和下一步；无明确状态不得进入 E2E Gate。

## Step 034：编写一键 E2E Demo Runner

- 做什么：执行“导入知识→注入邮件→运行图→查看草稿→模拟飞书审批→模拟发送→输出审计摘要”。
- 选型：`scripts/run_demo.py`、固定 fixture、空数据目录启动。
- 场景拷问：连续运行两次会生成两封模拟邮件吗？不能，第二次应报告去重或已完成。
- 验收/失败：新开发者一条命令可复现；失败时保留诊断路径，不清空证据后再重跑。

## Step 035：Level 1 Demo Gate

- 做什么：从干净环境执行全流程，发布 `v0.1.0-demo`，记录 commit、配置和测试报告。
- 选型：Mock Gmail、Mock LLM、Mock 飞书、Mock 外发；`AUTO_SEND=false` 永久默认。
- 场景拷问：只生成一段回复文本是否算 Demo？不算，必须证明入站、持久化、知识来源、审批、模拟外发、幂等和失败。
- 验收：12 项全部满足：入站、原文、检索证据、状态可追踪、草稿、审批、无未审批外发、批准后 outbox、Mock 飞书、重复幂等、失败状态、干净环境可启动。
- 失败处理：任一项失败就停在 Level 1，回退到最近通过 Gate 的 commit，不接真实 Gmail/飞书。

---

# Part III：Level 10–20——持久化底座和真实外部接入（Step 036–055）

## Step 036：迁移到 PostgreSQL 生产数据模型

- 做什么：将 Demo 表迁移为租户、邮箱、线程、消息、Run、Approval、Outbox、Profile、Knowledge、Audit 等正式表。
- 选型：PostgreSQL 16 + SQLAlchemy/Alembic；SQLite 仅保留本地离线模式。
- 场景拷问：多个客户共用实例时，任何查询是否都显式带 tenant_id？Repository 层和数据库策略双重保证。
- 验收/失败：迁移、索引、唯一约束和连接池压测通过；迁移失败时保留兼容旧表，不直接删除数据。

## Step 037：实现租户、身份和数据库隔离

- 做什么：所有业务表、队列键、Blob 键、Cache 键和 Graph config 强制携带 tenant_id。
- 选型：每客户独立部署作为物理隔离；未来共享实例增加 PostgreSQL RLS + 应用层过滤。
- 场景拷问：攻击者伪造 tenant_id 或重放旧 Token 能否读到其他客户？必须被认证层、Repository 和 RLS 共同拒绝。
- 验收/失败：跨租户读取/写入成功数为 0；命中安全事件时立即撤销会话并阻断租户。

## Step 038：部署持久化 LangGraph Checkpointer

- 做什么：保存 thread_id、run_id、state_version、graph_version、checkpoint_id 和小型状态快照。
- 选型：PostgresSaver；Redis 只做协调，不能作为唯一 Checkpoint。
- 场景拷问：Worker 在发送前崩溃，恢复是否会越过审批？恢复必须从安全节点继续并再次执行发送守卫。
- 验收/失败：杀死 Worker、断开数据库、并发 resume 后不丢状态和不重复副作用；损坏 Checkpoint 转人工。

## Step 039：建立 LangGraph Store 长期记忆

- 做什么：保存客户画像事实、对话摘要、反馈和版本，命名空间为 `(tenant_id, customer_key, kind)`。
- 选型：LangGraph Store/Repository；硬事实结构化存储，软风格只存受限特征。
- 场景拷问：Thread A 和 B 并发更新同一画像，是否最后写入覆盖？不允许，使用 profile_version/CAS 和语义合并。
- 验收/失败：每个事实有来源、证据、置信度和版本；冲突标记 `CONFLICT`，不让模型猜。

## Step 040：建立生产 Blob/FileBackend

- 做什么：将 EML、附件、快照和大文本迁移到对象存储，Graph 只保存 URI、hash、大小和版本。
- 选型：MinIO S3 API；云端部署可切 AWS S3/GCS/OSS；DeepAgent 使用受限 CompositeBackend。
- 路由：`/workspace→StateBackend`、`/knowledge→只读 FileBackend`、`/memories→StoreBackend`、`/artifacts→BlobStore`。
- 场景拷问：签名 URL 被转发后是否永久可用？必须短时有效并绑定权限。
- 验收/失败：跨租户键猜测、过期 URL、版本恢复和删除传播测试通过；失败文件进入隔离区。

## Step 041：实现可靠 Inbox/Outbox

- 做什么：事件先写 Inbox，业务事务同时写 Outbox，发布器可靠投递任务；记录 attempts、lease、last_error。
- 选型：PostgreSQL 事务 + Outbox Poller；成熟后评估 CDC。
- 场景拷问：数据库提交成功但消息发布失败怎么办？Outbox 保持 pending，后台重试，不允许人工直接删除。
- 验收/失败：提交后宕机、重复发布、ack 丢失和半成功测试通过；孤儿事件进入 DLQ。

## Step 042：建立 Redis Streams 任务队列

- 做什么：拆分 `fast/deep/profile/followup/manual-retry` 队列，设置消费组、租约、重试和优先级。
- 选型：Redis Streams；队列消息只存引用和版本，不塞邮件正文。
- 场景拷问：DeepAgent 高峰是否饿死审批恢复？审批恢复和普通回复保留并发配额。
- 验收/失败：消费者重启后任务可重新领取；积压和最老等待时间可观测。

## Step 043：建立 Scheduler 骨架

- 做什么：扫描到期跟进、续订 Gmail watch、知识重建和 GC 任务，生成可幂等队列消息。
- 选型：独立 scheduler Worker + 数据库时间索引；不把长任务放 FastAPI BackgroundTasks。
- 场景拷问：两个 Scheduler 同时扫描同一任务怎么办？使用租约、唯一任务键和原子状态变更。
- 验收/失败：重复扫描不重复建任务；扫描失败可以从上次游标继续。

## Step 044：建立备份和恢复的开发演练

- 做什么：备份 PostgreSQL、MinIO 元数据/对象、配置版本和迁移记录，恢复到新环境。
- 选型：pg_dump/PITR 预留、MinIO versioning；密钥不与数据备份明文混放。
- 场景拷问：只恢复数据库不恢复附件会怎样？恢复验证必须检查 URI、hash 和对象可读性。
- 验收/失败：恢复后能查询 Run、Checkpoint、草稿和原文；失败时禁止宣称“备份可用”。

## Step 045：建立保留、归档和 GC

- 做什么：区分活跃 Thread、终态摘要、审计保留、法务留存、Checkpoint 中间快照和附件 TTL。
- 选型：按租户配置 retention；只删除明确过期对象，先标记再异步清理。
- 场景拷问：客户删除请求后，索引、备份、DLQ 是否仍有 PII？删除传播必须有清单和验证任务。
- 验收/失败：归档不影响回放所需元数据；清理失败进入合规工单，不静默标记完成。

## Step 046：配置真实 Gmail OAuth

- 做什么：创建 Google Cloud 项目、OAuth Consent Screen、Authorization Code + PKCE、state/nonce 和精确 redirect URI。
- 选型：最小 Scope：`gmail.readonly`、`gmail.send`；`gmail.modify` 只有在确有标记已读需要时启用。
- 场景拷问：OAuth 被撤销或账号改名怎么办？暂停该 Mailbox 并通知重新授权，不影响其他租户。
- 验收/失败：授权、拒绝、刷新、撤销、错误 redirect 测试通过；Token 永不进入日志、Prompt 或 Checkpoint。

## Step 047：加密 Token 和密钥轮换

- 做什么：Envelope Encryption、Token 版本、刷新、撤销、访问审计和轮换流程。
- 选型：开发使用 Docker secrets；生产使用 KMS/Vault 兼容服务。
- 场景拷问：数据库泄露后 Token 能否直接使用？密文、KMS 权限和应用身份必须分离。
- 验收/失败：旧密钥失效、无停机轮换和暴露凭据应急撤销测试通过；泄露时立即暂停连接器。

## Step 048：建立 Gmail Pub/Sub Watch

- 做什么：为每个 Mailbox 建 watch、topic、push subscription 和 HTTPS endpoint，续订过期 watch。
- 选型：Google Pub/Sub Push；定时 history.list 作为补偿路径。
- 场景拷问：推送延迟数小时、重复推送或 watch 过期怎么办？Inbox 去重 + 续订 + 轮询补偿。
- 验收/失败：测试邮箱新邮件在目标窗口进入 Inbox；Pub/Sub 不可用时切换补偿并告警。

## Step 049：实现 Gmail History 增量同步

- 做什么：保存 historyId，调用 history.list，再拉取 message/thread/label；historyId 失效时全量重建。
- 选型：增量同步优先，按时间窗口全量校准为备选。
- 场景拷问：用户删除或移动标签导致幽灵邮件怎么办？记录删除变更并定期与 Gmail 抽样对账。
- 验收/失败：增量与 Gmail 抽样一致率 T≥99.9%；history 失效则标记 stale 并重建，不能继续使用旧游标。

## Step 050：实现 Gmail Provider 正式契约

- 做什么：统一 `watch/fetch/list_history/send/mark_read` 能力声明、错误分类和 provider message ID 映射。
- 选型：Protocol/ABC + Adapter Contract Tests；核心图不依赖 Google 原始 JSON。
- 场景拷问：Gmail API 字段变化是否要改 Graph？不应需要，只改 Adapter 映射。
- 验收/失败：Mock 和 Real Provider 通过相同契约测试；不支持的能力显式返回 `CapabilityNotSupported`。

## Step 051：建立 Gmail 配额和限流

- 做什么：按租户、Mailbox、API 方法实施 Token Bucket、并发信号量、Retry-After 和公平调度。
- 选型：Redis 令牌桶 + 队列延迟；不能仅依赖 Google 429 后无限重试。
- 场景拷问：一个大客户批量同步是否拖垮所有客户？租户上限和保留并发必须生效。
- 验收/失败：429、突发流量和公平性压测通过；超配额任务延迟而不是丢失。

## Step 052：创建真实飞书审批应用

- 做什么：创建租户级/实例级应用、卡片模板、回调加密校验、审批人映射和权限。
- 选型：飞书开放平台交互卡片；字段以版本化模板定义，不硬编码 UI。
- 场景拷问：不同客户审批人和卡片字段不同怎么办？通过 `ApprovalChannel` 配置和能力声明适配。
- 验收/失败：发送、编辑、拒绝、转交、超时和撤回都能产生业务事件；字段缺失转人工。

## Step 053：实现飞书回调幂等和重放防护

- 做什么：校验签名、时间窗、event_id、approval_code、instance_code 和版本；重复回调只产生一次副作用。
- 选型：Inbox 唯一约束 + 主动查询飞书最终状态。
- 场景拷问：先收到 approve 后收到 reject 哪个生效？以飞书最终状态和本地版本规则裁决，冲突进入人工。
- 验收/失败：伪造、延迟、乱序、重复回调测试通过；无法确认时不恢复发送。

## Step 054：完成外部连接器契约测试

- 做什么：对 Gmail、飞书、LLM、Blob、Queue 编写正常、超时、429、5xx、权限和不支持能力测试。
- 选型：pytest + HTTPX mock/VCR；生产不把真实账号放 CI。
- 场景拷问：供应商成功响应后网络断开怎么办？Adapter 必须把状态标记为 unknown，并交给补偿流程。
- 验收/失败：每个 Adapter 有错误映射和幂等说明；缺测试的连接器不能进入 staging。

## Step 055：Level 20 Staging Gate

- 做什么：在独立 staging Gmail、飞书和数据库上跑真实影子接入，不发送客户邮件。
- 选型：staging 租户、独立 OAuth Client、独立 Topic/Bucket/数据库。
- 场景拷问：测试环境是否能访问生产 Gmail 或生产 Bucket？必须由平台策略和凭据双重阻止。
- 验收：真实入站、事件去重、审批回调、Checkpoint 恢复和权限审计通过；不通过则撤销 staging 授权并回到 Mock。

---

# Part IV：Level 30–40——LangGraph、DeepAgent、知识和画像（Step 056–075）

## Step 056：固化外层业务 LangGraph

- 做什么：实现 `load_event→normalize→load_context→triage→route→reply/profile→fact_check→approval→send_guard→send→followup→outbox`。
- 选型：单一持久化 LangGraph；每个节点输入输出明确，瞬态字段使用覆写而不是无限累加。
- 场景拷问：节点执行顺序能否被 Agent 自由改变？不能，业务生命周期由主图固定。
- 验收/失败：合法状态转移率 T≥98%；非法边不可达，错误进入安全终态。

## Step 057：实现 interrupt/resume

- 做什么：在发送、高风险工具、人工画像修正和无法证实时 interrupt；飞书回调以受控 Command 恢复。
- 选型：LangGraph `interrupt`/`Command(resume=...)`；恢复事件签名并幂等。
- 场景拷问：审批卡片打开三天后知识或客户状态变化怎么办？恢复前重新加载控制状态和版本，旧草稿可过期。
- 验收/失败：批准、拒绝、超时、重复点击、审批人变更测试通过；超时默认转人工。

## Step 058：实现状态版本和 Graph 版本

- 做什么：Checkpoint 保存 `graph_version/state_schema_version/prompt_version/knowledge_snapshot_id`。
- 选型：版本化 State Adapter；旧任务优先用旧图完成，新任务用新图。
- 场景拷问：新版删除节点导致旧 Checkpoint 无法反序列化怎么办？不强行迁移，转兼容 Worker 或人工。
- 验收/失败：滚动升级和旧新版本混跑通过；迁移不可逆时采用前向修复并保留审计。

## Step 059：实现 Thread 级并发控制

- 做什么：同一 `tenant_id+thread_id` 串行；不同 Thread 可并发；画像写入按客户键串行。
- 选型：队列分区 + PostgreSQL advisory lock/行锁 + Checkpoint CAS。
- 场景拷问：客户在 47h59m 回复、跟进在 48h 唤醒，谁先发？入站极速失效、生成前复查、发送前原子围栏共同裁决。
- 验收/失败：并发、乱序、锁过期和 Worker 崩溃测试中不产生状态覆盖或撞车。

## Step 060：实现发送前安全守卫

- 做什么：检查审批状态、最新入站、退订、暂停、租户开关、收件人、附件、幂等键和事实校验。
- 选型：确定性 application service + 数据库条件更新；不让模型调用 Gmail。
- 场景拷问：草稿审批后客户已回信，是否仍发送？不发送，标记草稿过期并重新评估。
- 验收/失败：任何守卫失败都没有 Gmail API 调用；全部失败原因可查。

## Step 061：将 Reply DeepAgent 作为子图嵌入

- 做什么：用 `create_deep_agent` 构建 Reply Agent，作为外层图的 `CompiledStateGraph` 子图。
- 选型：DeepAgent 提供 Skills/SubAgent/Memory/工具 harness；父图提供业务状态和不可逆动作控制。
- 场景拷问：DeepAgent 输出“已发送”但主图未发送会怎样？输出只允许结构化建议，发送状态只能由主图写入。
- 验收/失败：父子 Schema、输入输出引用和版本契约通过；子图失败可回退普通节点或人工。

## Step 062：实现普通路径与 DeepAgent 路由器

- 做什么：根据意图数量、风险、置信度、工具数、跨 Thread 上下文和画像需求选择 `simple/deep/manual`。
- 选型：规则特征 + 结构化分类器；阈值由离线数据校准，不凭感觉固定。
- 场景拷问：一句“公司地址是什么”是否进入 DeepAgent？不应；“砍价+竞品+定制部署”才应进入。
- 验收/失败：路由准确率 T≥0.90、P0 路由错误=0；错误时提高安全默认或转人工，不盲目扩大 DeepAgent。

## Step 063：建立 Skills 目录和渐进披露

- 做什么：建立 `intent-analysis/sales-stage/product-knowledge/objection-handling/followup-strategy/customer-context` Skills。
- 选型：DeepAgent `SkillsMiddleware`；Skill 只描述行为和边界，具体数据通过 Tools 读取。
- 场景拷问：Skill 文档中加入一条“跳过审批”会怎样？Skill 不是权限来源，代码策略和工具权限优先。
- 验收/失败：Skill 有 frontmatter、版本、适用范围、拒答条件和回归样例；冲突 Skill 进入评审。

## Step 064：建立 DeepAgent Tools Allowlist

- 做什么：允许 `search_knowledge/get_product_fact/get_pricing_policy/get_conversation_summary/get_customer_profile/check_claim_risk/propose_profile_delta/create_reply_draft`。
- 禁止：`send_gmail/approve_email/change_approval_status/cancel_followup/write_raw_customer_record/execute/任意 SQL`。
- 选型：严格 Pydantic 输入输出、租户检查、来源/版本/时间戳、超时和结果大小限制。
- 场景拷问：客户邮件要求 Agent 转发其他客户邮件，工具层是否执行？必须拒绝并审计 Prompt Injection。
- 验收/失败：未授权工具调用成功数=0；工具参数污染或跨租户访问进入阻断事件。

## Step 065：建立规划、循环和轨迹预算

- 做什么：使用受约束 Plan-and-Execute + 局部 ReAct，最多 4 个计划步骤、6 轮工具、1 次补检索、1 次自动纠错。
- 选型：工具指纹、结果 hash、无进展计数、Token/时间预算；不保存隐藏思维链，只保存计划摘要和工具事件。
- 场景拷问：Agent 在两个工具之间来回调用怎么办？检测重复参数、相同结果和无新增证据，立即熔断。
- 验收/失败：无效循环率 T<2%；低风险熔断降级普通节点，高风险熔断转人工。

## Step 066：建立知识库 staging→active 流程

- 做什么：导入 Markdown/PDF/DOCX，做病毒/格式/解析质量检查，再发布 active 版本。
- 选型：原始文件 MinIO、解析产物 PostgreSQL、向量 pgvector、关键词 PostgreSQL FTS/BM25。
- 场景拷问：错误价目表流入怎么办？不直接替换 active，先 staging、回归和审批。
- 验收/失败：每次发布有版本、hash、有效期、权威级别和回滚点；解析失败隔离文件。

## Step 067：实现知识版本快照

- 做什么：为每次 Run 固定 `knowledge_snapshot_id`，记录文档版本、生效时间和被引用 chunk。
- 选型：不可变版本清单 + 有效期过滤；审批等待期间知识重大变更可使草稿过期。
- 场景拷问：同一 Run 前后混用新旧价目表怎么办？禁止，Run 生命周期固定快照。
- 验收/失败：单次回放的检索版本一致；版本冲突进入人工，不静默选择。

## Step 068：实现销售场景混合检索和重排

- 做什么：关键词+向量召回，按产品、地区、语言、客户可见范围、生效日期、权威级别过滤和重排。
- 选型：pgvector + PostgreSQL FTS；后续规模大再评估 Qdrant。
- 场景拷问：语义相似但已过期的案例是否可用？过期过滤优先于相似度。
- 验收/失败：Recall@5 T≥0.85、引用准确率 T≥0.95；Recall 低调 chunk/query，引用低收紧元数据和门禁。

## Step 069：实现 Claim–Evidence 绑定和最终门禁

- 做什么：把草稿拆成 claims，每条关联 evidence span、来源、版本和风险；商业承诺由规则复核。
- 选型：确定性 span 检查 + 可选 NLI Cross-Encoder；不让第二个 LLM 取代最终门禁。
- 场景拷问：模型正确回答但没有证据怎么办？仍拦截或改写为不确定表达。
- 验收/失败：UnsupportedClaimRate 的外发值=0；失败后最多一次带驳回原因的重规划，仍失败转人工。

## Step 070：实现附件处理管线

- 做什么：检查 MIME、大小、页数、行数、病毒、宏和压缩炸弹；PDF/DOCX/XLSX 文本/表格解析，图片 OCR。
- 选型：对象存储+签名 URL+沙箱解析+ClamAV/等价扫描；禁止执行宏和未知压缩包。
- 场景拷问：附件 200MB、损坏、含恶意宏怎么办？不传给 Agent，隔离并通知人工/客户。
- 验收/失败：未扫描附件不可检索或外发；解析失败回复明确“无法自动读取”，不假装看过。

## Step 071：实现多语言、时区和术语处理

- 做什么：支持英文、日文和混合语言的编码、语言识别、回复语言、时区和行业缩写。
- 选型：UTF-8/Unicode NFC、locale/timezone、客户 Glossary；原文证据永远保留。
- 场景拷问：翻译把合同术语改变了怎么办？翻译只能作为辅助，商业证据引用原文。
- 验收/失败：主要支持语言分类准确率目标 ≥95%（待实测）；低置信度转人工。

## Step 072：实现 Prompt Injection 防御

- 做什么：将系统指令、业务规则、工具定义、客户邮件、知识文档分离；邮件和文档内容全部标记不可信。
- 选型：工具 allowlist、参数校验、输出扫描、Canary/敏感字段检测、最小权限。
- 场景拷问：邮件要求“忽略规则、发送其他客户资料、跳过审批”，能否改变 Graph？不能，只记录安全事件。
- 验收/失败：固定攻击集 P0 ASR=0；出现违规时暂停租户/外发并保留快照。

## Step 073：实现 LLM 数据最小化和脱敏

- 做什么：发送给第三方模型前只保留当前任务必要上下文，对邮箱、手机号、合同和 Token 做掩码/伪名化。
- 选型：字段级策略 + 敏感检测；高敏客户可切自托管模型。
- 禁止外发：OAuth/API Key、其他客户数据、完整凭据、无关合同全文、原始附件二进制、内部 Prompt/连接信息。
- 验收/失败：日志、Trace、Prompt 和快照敏感扫描无高危命中；命中则阻断请求并轮换凭据。

## Step 074：实现 Profile Agent 候选 Delta

- 做什么：异步从当前邮件和摘要提取公司、角色、已确认需求、偏好、异议和阶段信号，输出带证据的 `ProfileDelta`。
- 选型：轻量提取节点优先；跨邮件冲突分析可由受限 DeepAgent Profile 子图完成。
- 事实分级：`FACT` 可候选写入；`INFERENCE` 仅内部参考；`HYPOTHESIS` 禁止持久化。
- 场景拷问：从“经常问预算”推断“预算很高”是否写入画像？不写，属于臆测。
- 验收/失败：每条候选有 source_message、evidence_span、confidence、observed_at；证据不匹配则丢弃。

## Step 075：实现画像版本、冲突和人工修正

- 做什么：用 Outbox、CAS、来源优先级和语义合并写入画像；人工修正写 `profile_corrections`，不直接改旧 Checkpoint。
- 选型：按客户键串行消费 + profile_version；人工修改通过 Graph 受控 update/resume。
- 场景拷问：CRM、邮件签名和人工给出三个不同职位，哪个生效？保留来源和冲突，必要时人工确认，不能猜。
- 验收/失败：画像事实可追溯、并发无丢失；冲突率异常时暂停画像自动写入并进入复核。

---

# Part V：Level 50–70——审批、发送、跟进、异常和安全（Step 076–094）

## Step 076：把飞书审批接入主图

- 做什么：将 `PENDING_APPROVAL` 映射为飞书卡片，approve/edit/reject/reassign 以版本化命令恢复 Graph。
- 选型：`ApprovalChannel` Adapter；飞书只做人工决策界面，不持有业务事实。
- 场景拷问：飞书卡片显示旧草稿但知识已更新怎么办？卡片带 draft hash/snapshot，恢复时重新校验。
- 验收/失败：卡片、审批、Graph 状态和审计一致率 T≥99.9%（待实测）；冲突默认阻断。

## Step 077：实现编辑、拒绝和审批审计

- 做什么：保存原始草稿 hash、人工终稿 hash、操作者、时间、理由和修改 Diff；编辑后重新走事实门禁。
- 选型：字段级/句子级 Diff + 审计表；不允许通过 UI 绕过校验。
- 场景拷问：人工把未经证实的价格加进草稿怎么办？最终安全门仍拦截并标高风险。
- 验收/失败：每次外发可回答“谁批准、改了什么、基于哪个版本”；审计缺失时不发。

## Step 078：实现 Gmail 幂等发送

- 做什么：发送前生成 `hash(tenant,thread,checkpoint,draft_hash)`，保存 send attempt，使用稳定 Message-ID 和唯一约束。
- 选型：PostgreSQL 唯一索引 + Adapter 幂等查询；Redis 只能做短期 in-flight 锁。
- 场景拷问：Worker 重试发送节点会不会发两封？命中 SUCCESS 直接返回原 message_id。
- 验收/失败：重复调用、并发调用、进程重启测试中副作用最多一次；异常转 unknown 而不是盲重试。

## Step 079：处理发送结果不确定

- 做什么：Gmail API 超时后查询 Sent、Thread、History 和 Message-ID，区分 sent/not-sent/unknown。
- 选型：补偿查询 + 人工队列；不能把 HTTP 200/超时简单等价为送达。
- 场景拷问：请求超时但实际已发送怎么办？查询到 message_id 后记为 SENT，禁止再次发送。
- 验收/失败：unknown 状态永不自动重发；状态可在后台补偿后闭合。

## Step 080：实现 Follow-up 状态机

- 做什么：定义 `SCHEDULED→GENERATING→PENDING_APPROVAL→SENT`，以及 `INVALIDATED/CANCELLED/EXPIRED/FAILED`。
- 选型：数据库状态 + Scheduler；每个 Thread 同时最多一个活动计划。
- 场景拷问：客户新邮件到达后已有计划怎么办？入站立即标记 INVALIDATED。
- 验收/失败：新邮件、退订、投诉、人工接管都会失效旧计划；状态冲突进入人工。

## Step 081：实现跟进“绝对零撞车”防线

- 做什么：入站极速失效、调度双检、Thread 锁、生成前复查、发送前行锁条件更新和幂等键。
- 选型：PostgreSQL row lock + Redis/Advisory lock；最终裁决在数据库。
- 场景拷问：47h59m59s 客户回复、48h 调度唤醒，如何保证不发？发送前条件必须确认 `last_inbound_time < generation_start` 且状态仍 GENERATING。
- 验收/失败：撞车事故数 T=0；任何一次违反都触发 P0 告警、暂停外发和故障复盘。

## Step 082：实现全局、租户、客户和 Thread 暂停

- 做什么：提供 `automation_controls` 和 `POST /pause/resume/cancel`，发送与调度前检查控制版本。
- 选型：数据库控制表 + Worker cancel/resume；暂停不靠删除 Redis 任务。
- 场景拷问：暂停时已有审批卡片或正在生成的 Agent 怎么办？草稿过期、运行中断、Outbox 阻塞，恢复后重新校验。
- 验收/失败：global/tenant/customer/thread 四层开关均可生效；无法确认开关状态时默认不发。

## Step 083：建立版本化业务策略配置

- 做什么：配置跟进间隔、最大次数、退订抑制、语言、模型路由、风险规则和租户限额。
- 选型：YAML/数据库版本化配置 + 生效时间 + 审批；不把频次写死在 Prompt。
- 场景拷问：运营想把行业跟进从 48h 改为 24h，是否改代码？不需要，但配置变更要审计和可回滚。
- 验收/失败：策略版本写入 Run 快照；配置解析失败时采用安全默认并告警。

## Step 084：建立错误分类和可解释错误码

- 做什么：区分用户错误、权限错误、数据错误、模型错误、供应商错误、网络瞬态、系统故障和未知故障。
- 选型：领域错误码 + 内部 runbook 链接；对外隐藏堆栈和敏感细节。
- 场景拷问：用户看到“失败”还是“需要重新授权/等待审批/修复附件”？错误消息必须可行动。
- 验收/失败：每个错误码可关联 trace、重试策略和责任人；未知错误进入安全终态。

## Step 085：实现重试、退避、熔断和预算

- 做什么：瞬态错误指数退避+jitter，尊重 Retry-After，设置最大尝试数、节点超时、总运行超时和熔断。
- 选型：任务队列重试；不可重试的权限/参数错误直接人工；DeepAgent 预算独立控制。
- 场景拷问：模型 429 时是否无限重试？不无限重试，排队、切备用模型或降级模板。
- 验收/失败：每次重试有原因、次数、幂等键；达到上限进入 DLQ，不重复副作用。

## Step 086：建立 Dead Letter Queue 和安全重放

- 做什么：保存毒消息、失败 Run、错误堆栈引用、版本、重试历史和人工处理结果，支持按键重放。
- 选型：独立 `manual-retry` 队列 + 管理接口；重放前必须重新检查版本、暂停和幂等。
- 场景拷问：旧版本任务重放到新图会不会行为漂移？默认用原版本或明确迁移，不隐式切换。
- 验收/失败：DLQ 新增告警、人工重放可审计；重放失败仍留在 DLQ，不循环重放。

## Step 087：实现 API 认证、RBAC 和 ABAC

- 做什么：保护状态查询、审批、配置、画像修正、DLQ 重放和紧急停止，按租户/角色/数据范围授权。
- 选型：短期 API key/JWT，生产 OIDC/OAuth；工具层和 Repository 再做资源级检查。
- 场景拷问：运营人员能否访问其他租户的 Trace？不能，连错误消息也不得泄露存在性。
- 验收/失败：未授权、越权、重放 Token 测试全部阻断；权限异常触发安全事件。

## Step 088：实现 OAuth Scope 和密钥轮换治理

- 做什么：代码和 Google Cloud/飞书平台双重锁定最小权限，建立撤销、轮换、离职和泄露响应流程。
- 选型：Gmail readonly/send，按需 modify；不申请 delete、settings、contacts 等无关权限。
- 场景拷问：Agent 是否能删除客户邮件、改标签或读其他邮箱？它看不到这些工具，Adapter 也不实现。
- 验收/失败：Scope 审计和代码 allowlist 一致；发现过宽权限时暂停发布并重新授权。

## Step 089：完成安全负向测试和攻击演练

- 做什么：测试 Prompt Injection、越权、跨租户、SSRF、恶意附件、Token 泄露、敏感信息回显和 RCE 风险。
- 选型：SAST、依赖扫描、DAST、红队攻击集、隔离沙箱；Agent 禁止 Shell。
- 场景拷问：知识文档中的“跳过审批”能否成为系统指令？不能，文档内容仅为检索证据。
- 验收/失败：P0/P1 漏洞上线前为 0，P0 ASR=0；失败立即阻断发布并复测。

## Step 090：接入 OpenTelemetry 全链路 Trace

- 做什么：将 HTTP traceparent/X-Trace-Id 透传到队列、RunnableConfig、LangGraph 节点、LLM callback、数据库事件。
- 选型：OpenTelemetry + OTLP；日志、Trace 和审计使用同一 correlation key。
- 场景拷问：用户说“邮件没处理”，能否从 Gmail event 找到最后节点？必须能。
- 验收/失败：关键链路 Trace 完整率 T≥95%（生产目标≥98%，待实测）；丢失则补埋点，不把日志复制为答案。

## Step 091：建立业务、AI、系统三类指标看板

- 做什么：分别监控入站延迟、路由/阶段、RAG/事实、人工修改、审批、跟进、成本、队列和错误。
- 选型：Prometheus/Grafana/Loki + LangSmith 可选；正文不进普通指标标签。
- 场景拷问：0 修改直发率下降如何定位？按租户、语言、模型、Prompt、Knowledge Snapshot 和 Diff 类别下钻。
- 验收/失败：历史故障能触发告警并定位版本；无人采取行动的指标删除或降级。

## Step 092：建立成本账本和租户预算

- 做什么：记录模型输入/输出 Token、Embedding、RAG、工具、OCR、存储、队列和人工接管成本。
- 选型：`cost_ledger` 按 tenant/scene/route/node/model/version 聚合；预算 80/90/100% 分级。
- 场景拷问：一个超长 Thread 是否耗尽月度预算？限制上下文、DeepAgent 次数、并发和模型等级。
- 验收/失败：账单聚合与 Provider 误差 T≤5%（待实测）；超预算降级或暂停，不影响高风险人工通道。

## Step 093：完成容量、并发和资源隔离测试

- 做什么：测量 Gmail 高峰、普通回复、DeepAgent、审批恢复、画像和附件任务的吞吐、队列等待和内存。
- 选型：独立 Worker：`worker-fast/deep/profile/followup`；每租户并发上限和保留配额。
- 场景拷问：DeepAgent 大量占满 Worker，普通任务和审批是否饿死？独立队列/信号量和优先级必须保证。
- 验收/失败：普通任务、审批恢复和高复杂任务各有 P95 目标；超载时削峰和降级，不丢任务。

## Step 094：完成 Docker Compose 高可用基线

- 做什么：API 无状态、多 Worker、副本健康检查、数据库连接池、Redis 持久化、MinIO 版本化和自动重启。
- 选型：每客户独立 Compose；规模化后再评估 Kubernetes。
- 场景拷问：单个 Worker、Redis 或数据库短暂故障会怎样？任务从 Inbox/Checkpoint 恢复，非关键能力降级。
- 验收/失败：关键 API 可用性目标 T≥99.9%、RTO/RPO 由客户约定；单实例失败不造成数据丢失。

---

# Part VI：Level 80–100——版本、灾备、评测、灰度和正式交付（Step 095–100）

## Step 095：建立工作流、Schema、Prompt 和 Tool 迁移策略

- 做什么：采用 expand→backfill→switch→contract，版本化 Event、Checkpoint、Prompt、Skill、Tool Schema、Model 和 Knowledge。
- 选型：向后兼容 JSON Schema + State Adapter；数据库迁移与 Graph 版本分开发布。
- 场景拷问：旧审批挂起两天期间发布新图怎么办？旧 Run 用旧版本恢复，除非有经过测试的迁移器。
- 验收/失败：滚动升级、旧新消费者混跑、迁移中断和回滚测试通过；不兼容时保留旧 Worker。

## Step 096：完成 PITR、对象恢复和灾备演练

- 做什么：配置 PostgreSQL PITR/备份、MinIO 对象版本、配置备份、跨区域或异地副本，定期恢复到新环境。
- 选型：早期同区域可恢复，生产目标按客户约定 RPO/RTO；密钥和数据分开备份。
- 场景拷问：误删租户、数据库损坏、对象存储不可用时能否恢复到可验证状态？必须用实际演练证明。
- 验收/失败：建议目标 RPO≤15 分钟、RTO≤4 小时（待实测和客户约定）；不达标时限制写入并升级灾备事件。

## Step 097：建立事故响应、值班和紧急停止 Runbook

- 做什么：编写 LLM 故障、Gmail/飞书故障、重复外发、跨租户疑似泄露、DLQ、数据删除、回滚和恢复手册。
- 选型：P0/P1/P2 分级、轮值、备用通知渠道、global/tenant/customer/thread kill switch。
- 场景拷问：凌晨发生疯狗模式，值班人员能否 10 分钟内止损？必须先关外发、阻塞 Outbox、取消跟进并保留证据。
- 验收/失败：桌面演练和实战演练通过；Runbook 无法执行时保持人工/只读模式。

## Step 098：建立 Golden Dataset 和离线评测 Harness

- 做什么：构建 300–500 条起步数据，含真实脱敏、专家案例、合成边界、多语言、工具轨迹、附件和攻击样例。
- 选型：按租户/用户/时间/语义去重切分 train/dev/test/time-holdout；版本化数据集和标签指南。
- 标签：意图、风险、阶段、必答事实、允许动作、证据、工具选择、完整性、语气、追问、拒答和安全。
- 场景拷问：只用 happy path 自评是否可信？不可信，必须含至少 20% 边界、10% 安全负向和时间留出集。
- 验收/失败：双人标注一致性 T≥0.75，P0 标签 100% 一致；数据泄漏发现后重新切分。
- 评测：程序化 Schema/权限/证据硬约束 + 人工/LLM Judge 语义评分；LLM Judge 只做排序和预警，P0 门禁不由它单独决定。

## Step 099：完成回放、影子、A/B 和持续优化闭环

- 做什么：保存脱敏快照（邮件引用、画像版本、阶段、工具事件、证据、草稿、人工 Diff、模型/Prompt/Skill/Knowledge 版本），支持单变量回放。
- 选型：影子流量不触发外部副作用；稳定 hash 分桶，1%→5%→25%→50%→100% 灰度；主指标+安全/成本/延迟护栏。
- 场景拷问：新版本离线分数提高但生产成本翻倍或人工修改增加，是否全量？不全量，按分层指标和护栏决定。
- 验收/失败：质量下降>2 个百分点、P95 增长>15%、成本增长>10%或任何 P0 事件自动回滚；阈值需结合真实基线校准。
- 优化分类：事实错误→知识/证据门禁；漏答→Schema/Skill/Prompt；工具错误→Tool 契约；路由错误→Router；状态错误→Graph/锁；成本错误→上下文/模型分层。

## Step 100：企业级正式验收和可运营交付

- 做什么：对功能、安全、可靠性、AI 质量、成本、性能、部署、文档和运营逐项签字，发布正式版本并交付客户。
- 生产验收必须同时满足：
  - 真实 Gmail OAuth、Pub/Sub、Thread 增量同步和真实飞书审批可恢复；
  - 外层 LangGraph Checkpoint 可持久化、暂停、恢复、迁移或安全转人工；
  - DeepAgent 复杂路由、Skills、Tools、循环熔断和最终事实门禁可解释；
  - 未审批外发=0、跟进撞车=0、跨租户读取成功=0、高风险无证据外发=0；
  - Inbox/Outbox、幂等发送、发送 unknown 补偿、重试、DLQ、备份恢复和紧急停止均通过故障演练；
  - Golden Dataset、时间留出集、安全集、回放、影子、A/B、灰度和自动回滚可运行；
  - 运营人员可以重授权、暂停/恢复租户、查看审计、重放 DLQ、处理人工队列、导出/删除数据和修改版本化策略；
  - 交付包包含 Compose、配置、Gmail/飞书手册、知识库规范、监控面板、Runbook、备份恢复、升级回滚、数据处理和已知限制。
- 场景拷问：上线后谁负责模型升级、知识更新、供应商变更、数据删除和事故响应？必须在责任矩阵中明确 Owner、SLA 和回滚人。
- Level 100 判定：不是“代码能跑”，而是系统在真实外部依赖、失败、攻击、成本压力和运营交接下仍能安全工作；任一 P0 门槛不通过，只能标记为受限 GA，不能宣称完整企业级交付。

---

## 3. Level 100 之后的持续运营节奏

Level 100 不是项目终点，而是可持续优化的起点：

### 每日

- 检查 P0/P1 告警、未审批外发、撞车、DLQ、LLM 错误率、队列积压、成本异常和数据脱敏命中。
- 抽样查看普通路径、DeepAgent 路径和人工接管任务。

### 每周

- 分析 AI 草稿与人工终稿 Diff，新增高价值 Bad Case 和回归样例。
- 检查 RAG 过期文档、引用准确率、路由分布、阶段抖动、工具循环和租户公平性。
- 只选择一个根因变量做 Prompt/Skill/Tool/Router/Knowledge 实验。

### 每月

- 按租户、场景、阶段、模型和版本复盘成本、质量、延迟、人工接管和跟进回复。
- 重新校准 DeepAgent 进入阈值、预算、跟进策略和灰度比例。
- 审核策略配置、OAuth Scope、数据保留和访问权限。

### 每季度

- 做一次完整故障注入、回滚、备份恢复、Prompt Injection 和权限演练。
- 更新攻击集、时间留出集、业务标签指南和灾备目标。
- 评估是否进入二期：CRM/Slack/Microsoft 365、营销画像、项目预警或风险分级自动发送。

持续优化的判断顺序固定为：

```text
先问是否是数据/知识问题
  → 再问是否是状态/权限/工具问题
  → 再问是否是路由/策略问题
  → 最后才考虑换模型或改 Prompt
```

这条顺序可以避免把工程故障伪装成“模型不够聪明”，也能避免用更昂贵的模型掩盖数据、权限和流程缺陷。

---

## 4. 交付前总清单

### 代码和部署

- [ ] 独立 Git、锁定依赖、CI、SBOM、Compose、迁移和一键启动
- [ ] API、Worker、Scheduler、PostgreSQL、Redis、MinIO 分工清晰
- [ ] Mock/Real Adapter 可切换且契约测试通过

### 业务闭环

- [ ] Gmail 入站、解析、去重、Thread、普通回复、DeepAgent、知识、画像
- [ ] 飞书审批、编辑、拒绝、转人工、暂停/恢复
- [ ] Gmail 幂等发送、unknown 补偿、跟进取消和零撞车

### 安全和合规

- [ ] OAuth 最小 Scope、Token 加密、租户隔离、RBAC/ABAC
- [ ] 日志/Trace/LLM/快照脱敏和访问审计
- [ ] Prompt Injection、越权、恶意附件、敏感信息和供应链测试

### AI 质量和运营

- [ ] Golden Dataset、时间留出集、安全集、回放和 LLM Judge 校准
- [ ] 路由、阶段、RAG、证据、工具轨迹、人工 Diff、成本和延迟指标
- [ ] 影子、A/B、灰度、自动回滚、Bad Case 和持续运营节奏

### 正式签字

- [ ] 业务确认成功定义和禁用边界
- [ ] 信息安全确认数据、权限和攻击测试
- [ ] 运维确认 SLO、备份、恢复、告警和值班
- [ ] 交付方确认培训、Runbook、支持窗口和变更责任

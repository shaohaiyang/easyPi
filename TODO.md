# easyPi 改进计划

> 基于 pydantic-ai 内核的多智能体旅行规划助手分析报告

---

## 当前技术栈

| 技术 | 用途 |
|---|---|
| **pydantic-ai** | 核心 AI Agent 框架（OpenAI 兼容模式） |
| **FastAPI + Uvicorn** | Web 框架 + ASGI 服务器 |
| **Jinja2** | 后端模板渲染（5 个 HTML 模板） |
| **Tailwind CSS (CDN)** | 前端 UI 样式 |
| **SSE（Server-Sent Events）** | 实时进度推送，`asyncio.Event` 协调前后端 |
| **asyncio** | `create_task` 后台规划 + `wait_for` 空闲超时 |
| **python-dotenv** | 环境变量加载 |
| **Pydantic** | 结构化输出模型校验 |
| **pytest** | 单元测试（4 个 model 构造测试） |

依赖：8 个库（`pyproject.toml`），无数据库，无 LLM 之外的第三方 API。

---

## 差距分析

### 架构层面

- [ ] **串行执行**：guide → foodie → local → finance → moderator 严格串行，前三个专家互不依赖却要等前一个跑完
- [ ] **无动态路由**：无论用户问什么都跑满 4 个专家
- [ ] **无容错重试**：任一专家失败则整体崩溃，只能报错不能局部重试
- [ ] **无工具调用**：专家只靠自身知识，无法查天气、票价、开放时间等实时数据
- [ ] **无记忆/多轮**：一次性请求，无法追问或迭代修改

### 体验层面

- [ ] **无流式输出**：等所有 LLM 跑完才展示结果，用户只能看进度条干等
- [ ] **进度百分比硬编码**：`10→30→50→70→85→90→100`，与实际耗时脱节
- [ ] **无结果质量评估**：主持人直接合成，不校验输出是否合规

### 工程层面

- [ ] **无数据库**：内存 dict 存 plans，服务重启数据全丢
- [ ] **无认证**：任何人知道 plan_id 即可访问
- [ ] **测试覆盖低**：仅 4 个 model 构造测试，无 agent 集成测试
- [ ] **Agent 是模块级单例**：单元测试无法 mock 替换，测试间互相污染
- [ ] **无日志/可观测性**：无 structured logging，排查问题困难

---

## 改进计划

### P0 — 快速见效

- [ ] **并行执行独立专家**（~30min）
  guide/foodie/local 三者不依赖彼此输出，用 `asyncio.gather` 并行，节省约 2/3 的串行等待时间

- [ ] **自适应进度估算**（~15min）
  把硬编码百分比改成 `progress_count / total_steps` 动态计算，加时间轴预测

### P1 — 稳定性和实用性

- [ ] **结构化输出校验 + 重试**（~1-2h）
  各专家使用更严格的 Pydantic output_type，捕获 `ModelRetry` 后自动修正提示词重试

- [ ] **添加 Web Search Tool**（~2-3h）
  给 moderator 加天气/票务信息查询 tool，利用 `@agent.tool` 机制

- [ ] **持久化（SQLite）**（~1h）
  用 `aiosqlite` + `plans` 表替换内存 dict

### P2 — 体验提升

- [ ] **多轮对话**（~4-6h）
  保持 `plan_id` 级别 conversation history，新增 `PATCH /plan/{plan_id}/refine` 接口

- [ ] **测试体系**（~3-4h）
  加 `conftest.py` + `pytest-asyncio`，mock LLM 调用写 agent 集成测试和端到端测试

### P3 — 长期优化

- [ ] **流式输出（Streaming via SSE）**（~4-6h）
  利用 `agent.run_stream()` 把 token 通过 SSE 推送到前端增量渲染

- [ ] **日志 + 链路追踪**（~2-3h）
  加 `structlog`，记录每次 LLM 调用的 prompt 长度、响应时间、token 用量

- [ ] **动态专家路由**（~3-4h）
  moderator 先用轻量判断需要咨询哪些专家，再启动对应专家

- [ ] **认证机制**（~2-3h）
  简单 token 或 session 认证，防止 plan_id 被遍历

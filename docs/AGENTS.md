# 多智能体助手构建经验

## 架构模式：主持人 + 专家团

```
用户输入 → 主持人 Agent → 依次调用专家 Agent → 主持人综合输出
```

- **主持人**：负责调度、上下文管理、最终合成。用最强/最快的模型。
- **专家**：每个专家只做一件事，职责单一。可以用便宜模型。
- **编排在应用层做**：不要依赖 Agent 框架的 tool-calling 做编排，直接在 Python 代码里按顺序调用各 Agent，可控性更高。

## 模型接入：统一网关

```python
OpenAIChatModel(
    "model-name",
    provider=OpenAIProvider(base_url="https://统一网关/v1", api_key="统一密钥"),
)
```

- 用火山引擎/OpenRouter 等统一网关，一个 endpoint + 一个 API key 管理所有模型
- 环境变量统一管理密钥，不硬编码
- 空密钥给 placeholder 避免 import 时崩溃，运行时才真正校验

## SSE 进度反馈

### 后端

```python
# progress.py
@dataclass
class ProgressTracker:
    current_stage: str
    message: str
    pct: int
    done: bool
    failed: bool
    _event: asyncio.Event  # 通知 SSE 生成器

    def update(stage, msg, pct):
        # 更新状态 + 唤醒 SSE
        self._event.set()

    def mark_failed(error):
        # 异常时设置失败状态
        self.failed = True
        self.done = True
        self._event.set()
```

```python
# routes.py - SSE endpoint
async def event_generator():
    while not tracker.done:
        await asyncio.wait_for(tracker._event.wait(), timeout=120)
        tracker._event.clear()
        if tracker.failed:
            yield error event
            return
        yield progress event
```

### 前端

```html
const evtSource = new EventSource("/plan/{id}/progress");
evtSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    // 更新进度条、图标、消息
    resetStallTimers(); // 每次进度更新重置空闲计时器
};
```

### 超时策略（关键）

- **不设总超时**：LLM 思考时间不定，固定总超时必然误伤
- **空闲超时**：后端 120s 无进度判定超时；前端 30s 无进度给提示，120s 判定失败
- **每次进度更新重置空闲计时器**：LLM 持续推进就永远不超时

## 失败处理三层保护

1. **后端异常捕获**：`create_plan` 整体 try/except，失败时 `tracker.mark_failed(error)`
2. **SSE 超时**：后端 120s 无事件 + 前端 120s 无事件
3. **前端连接断开**：EventSource onerror 自动重连，提示用户"别担心，进度已保存"

## 前端用户体验

- **进度条**：直观显示完成百分比
- **阶段图标切换**：🌏 导游 → 🍜 美食家 → 🏘️ 本地通 → 💰 财务官 → 🧠 主持人
- **安慰话术轮播**：等待时随机显示温柔提示，5 秒后开始轮播
- **完成状态独立页面**：绿色主题 + 弹跳 ✅ 动画，与规划中的蓝色主题完全区分
- **失败状态独立页面**：红色卡片 + 具体错误 + 重试按钮，自动复用表单数据

## 模板设计原则

- **圆角卡片化**：`.rounded-xl shadow-sm border border-gray-100`，清爽现代
- **疏朗间距**：大 `p-6/p-8`，足够的 `gap-4/gap-6`
- **分层展示**：景点/美食/贴士用 h4 标题 + list 区分
- **可折叠内容**：看板页讨论记录用 `<details>` 折叠，不占空间
- **移动端适配**：`grid-cols-1 md:grid-cols-2 lg:grid-cols-4` 渐进增强

## pydantic-ai 关键 API

```python
# Agent 构造
Agent(model, output_type=..., deps_type=..., instructions=...)

# 模型：OpenAI 兼容
OpenAIChatModel("model", provider=OpenAIProvider(base_url=..., api_key=...))

# DeepSeek 原生
Agent("deepseek:deepseek-chat")

# 运行
result = await agent.run(prompt, deps=..., usage=ctx.usage)

# 结构化输出
class MyOutput(BaseModel):
    field: str = Field(description="...")
```

## 项目结构模板

```
project/
├── .env                     # 密钥（不提交）
├── .env.example
├── pyproject.toml
├── src/
│   ├── app.py               # FastAPI 入口
│   ├── config.py            # 模型配置
│   ├── progress.py          # SSE 进度跟踪
│   ├── models/
│   │   └── output.py        # Pydantic 输出模型
│   ├── agents/
│   │   ├── moderator.py     # 主持人 + 编排逻辑
│   │   ├── expert_a.py
│   │   ├── expert_b.py
│   │   └── ...
│   └── web/
│       ├── routes.py
│       └── templates/
│           ├── base.html
│           ├── index.html       # 输入表单
│           ├── progress.html    # SSE 进度页
│           ├── result.html      # 结果页
│           └── dashboard.html   # 看板页
└── tests/
```

## 快速开始下一个项目

```bash
cp -r easyPi new-project
cd new-project
# 改 config.py 里的模型名
# 改 agents/ 里的专家角色和 instructions
# 改 models/output.py 里的输出结构
# 改 templates/ 里的展示
```

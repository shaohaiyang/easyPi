# easyPi - 多智能体旅游助手

基于 pydantic-ai 的多智能体旅游规划助手。主持人 + 4 专家讨论模式，输出结构化行程。

## 架构

```
用户输入（目的地/天数/预算/偏好）
        │
        ▼
┌─────────────────────────────────┐
│     Moderator Agent             │  deepseek-v4-flash-260425
│   (主持人，负责调度与综合)        │
└──────────┬──────────────────────┘
           │ agent delegation（依次调用）
     ┌─────┼─────┬─────┐
     ▼     ▼     ▼     ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│ Guide  ││ Foodie ││ Local  ││Finance │  glm-4-7-251222
│ 导游    ││ 美食家 ││ 本地通  ││财务官  │
└────────┘└────────┘└────────┘└────────┘
           │
           ▼
┌─────────────────────────────────┐
│    Structured Itinerary         │  Pydantic validated
│    (Pydantic output model)      │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   FastAPI + Jinja2 Web UI       │
│   讨论看板 + 行程展示            │
└─────────────────────────────────┘
```

### Agent 角色

| Agent | 模型 | 职责 |
|-------|------|------|
| 主持人 (Moderator) | DeepSeek V4 Flash | 接收用户需求，调度专家，综合输出 |
| 导游 (Guide) | GLM-4.7 | 路线规划、景点推荐 |
| 美食家 (Foodie) | GLM-4.7 | 餐厅推荐、本地美食 |
| 本地通 (Local Expert) | GLM-4.7 | 小众景点、文化贴士、交通建议 |
| 财务官 (Finance Officer) | GLM-4.7 | 预算分配、省钱建议 |

### 模型接入

所有模型通过火山引擎方舟统一网关接入，同一个 endpoint + API key。

## 快速开始

### 1. 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

`.env` 内容：
```
VOLC_API_KEY=your_volcengine_api_key
```

### 3. 运行

```bash
source .venv/bin/activate
python src/app.py
```

打开 http://127.0.0.1:8000

## 项目结构

```
easyPi/
├── pyproject.toml
├── .env                     # API Key（不提交）
├── .env.example             # 模板
├── .gitignore
├── tests/
│   └── test_models.py       # 模型测试
├── src/
│   ├── app.py               # FastAPI 入口
│   ├── config.py            # 火山引擎配置
│   ├── models/
│   │   └── itinerary.py     # Pydantic 输出模型
│   ├── progress.py          # SSE 进度跟踪
│   ├── agents/
│   │   ├── moderator.py     # 主持人 agent + 编排逻辑
│   │   ├── guide.py         # 导游
│   │   ├── foodie.py        # 美食家
│   │   ├── local_expert.py  # 本地通
│   │   └── finance.py       # 财务官
│   └── web/
│       ├── routes.py        # FastAPI 路由（含 SSE）
│       └── templates/
│           ├── base.html
│           ├── index.html      # 输入表单
│           ├── progress.html   # 进度页（进度条+安慰话术）
│           ├── plan.html       # 讨论+行程
│           └── dashboard.html  # 看板视图
└── docs/superpowers/
    ├── specs/                   # 设计文档
    └── plans/                   # 实现计划
```

## API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 输入表单 |
| `/plan` | POST | 提交需求，进入进度页，后台异步生成行程 |
| `/plan/{id}` | GET | 查看行程详情 |
| `/plan/{id}/progress` | GET | SSE 实时进度流 |
| `/dashboard/{id}` | GET | 看板视图 |

## 用户体验

生成行程时，页面通过 SSE (Server-Sent Events) 实时展示：

1. **进度条** — 直观显示整体完成度
2. **阶段提示** — 当前哪位专家在思考（导游/美食家/本地通/财务官/主持人）
3. **安慰话术** — 等待过程中随机显示温柔提示
4. **讨论日志** — 实时追加每位专家的思考结果

## 测试

```bash
source .venv/bin/activate
pytest tests/ -v
```

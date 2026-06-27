# Travel Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent travel assistant with moderator-led discussion, 4 specialist agents (DeepSeek + GLM), and a FastAPI + Jinja2 web dashboard.

**Architecture:** Moderator agent (DeepSeek) orchestrates 4 specialist agents (GLM) via agent delegation. Specialists return structured opinions; moderator synthesizes into a Pydantic-validated itinerary. FastAPI serves the web UI with SSE streaming for discussion progress.

**Tech Stack:** Python 3.12+, pydantic-ai, FastAPI, Jinja2, httpx, uvicorn

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `src/models/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "easy-pi"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic-ai[openai]>=0.1.0",
    "pydantic-ai[web]>=0.1.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "jinja2>=3.1.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.28.0",
]

[project.scripts]
travel-assistant = "src.app:main"

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Create .env.example**

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key
GLM_API_KEY=your_glm_api_key
```

- [ ] **Step 3: Create src/__init__.py** (empty)

- [ ] **Step 4: Create src/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")

DEEPSEEK_MODEL = "deepseek:deepseek-chat"
GLM_MODEL_NAME = "glm-4-plus"
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
```

- [ ] **Step 5: Create src/models/__init__.py** (empty)

- [ ] **Step 6: Install dependencies and verify**

Run: `cd /Users/shaohy/Github/easyPi && uv sync` or `pip install -e .`
Expected: no errors

---

### Task 2: Pydantic Output Models

**Files:**
- Create: `src/models/itinerary.py`

- [ ] **Step 1: Create src/models/itinerary.py**

```python
from pydantic import BaseModel, Field


class DailyPlan(BaseModel):
    day: int = Field(description="Day number (1-based)")
    date: str = Field(description="Date label, e.g. 'Day 1'")
    attractions: list[str] = Field(description="Places to visit this day")
    meals: dict[str, str] = Field(description="breakfast/lunch/dinner recommendations")
    budget: float = Field(description="Estimated budget for this day in CNY")
    tips: list[str] = Field(description="Local tips for this day")


class Itinerary(BaseModel):
    destination: str = Field(description="Travel destination")
    total_days: int = Field(description="Total trip duration in days")
    total_budget: float = Field(description="Total estimated budget in CNY")
    daily_plans: list[DailyPlan] = Field(description="Day-by-day plan")
    summary: str = Field(description="Trip summary and highlights")


class DiscussionEntry(BaseModel):
    agent_name: str
    content: str


class PlanResult(BaseModel):
    itinerary: Itinerary
    discussion: list[DiscussionEntry]
```

- [ ] **Step 2: Verify models import correctly**

Run: `cd /Users/shaohy/Github/easyPi && python -c "from src.models.itinerary import Itinerary, DailyPlan, DiscussionEntry, PlanResult; print('OK')"`
Expected: `OK`

---

### Task 3: Specialist Agents (Guide, Foodie, Local Expert, Finance)

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/guide.py`
- Create: `src/agents/foodie.py`
- Create: `src/agents/local_expert.py`
- Create: `src/agents/finance.py`

- [ ] **Step 1: Create src/agents/__init__.py** (empty)

- [ ] **Step 2: Create src/agents/guide.py**

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL
from src.models.itinerary import DailyPlan


guide_model = OpenAIChatModel(
    GLM_MODEL_NAME,
    provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
)

guide_agent = Agent(
    guide_model,
    result_type=list[str],
    instructions=(
        "You are a professional travel guide planner. "
        "Based on the user's destination, trip duration, and preferences, "
        "suggest a day-by-day list of attractions to visit. "
        "Return a list of strings, each describing one day's recommended attractions. "
        "Be specific with location names and consider reasonable travel routes between them."
    ),
)
```

- [ ] **Step 3: Create src/agents/foodie.py**

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL


foodie_model = OpenAIChatModel(
    GLM_MODEL_NAME,
    provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
)

foodie_agent = Agent(
    foodie_model,
    result_type=list[str],
    instructions=(
        "You are a local food expert. "
        "Based on the user's destination, trip duration, and the proposed itinerary, "
        "suggest breakfast, lunch, and dinner options for each day. "
        "Return a list of strings, each describing one day's meal recommendations. "
        "Include local specialties and budget-friendly options."
    ),
)
```

- [ ] **Step 4: Create src/agents/local_expert.py**

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL


local_model = OpenAIChatModel(
    GLM_MODEL_NAME,
    provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
)

local_agent = Agent(
    local_model,
    result_type=list[str],
    instructions=(
        "You are a local expert who knows hidden gems, culture, and practical tips. "
        "Based on the destination and itinerary, suggest: "
        "1) Hidden gems and off-the-beaten-path spots, "
        "2) Cultural etiquette and customs, "
        "3) Transportation tips between locations, "
        "4) Weather and packing advice. "
        "Return a list of strings, one tip per entry."
    ),
)
```

- [ ] **Step 5: Create src/agents/finance.py**

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL


finance_model = OpenAIChatModel(
    GLM_MODEL_NAME,
    provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
)

finance_agent = Agent(
    finance_model,
    result_type=dict,
    instructions=(
        "You are a travel finance officer. "
        "Based on the destination, duration, itinerary, and budget constraints, "
        "allocate budget for each day including: "
        "transportation, meals, attractions tickets, accommodation, miscellaneous. "
        "Return a dict with keys as day labels and values as budget breakdown strings. "
        "Provide total estimated cost and money-saving tips."
    ),
)
```

- [ ] **Step 6: Verify specialist agents import correctly**

Run: `cd /Users/shaohy/Github/easyPi && python -c "from src.agents.guide import guide_agent; from src.agents.foodie import foodie_agent; from src.agents.local_expert import local_agent; from src.agents.finance import finance_agent; print('OK')"`
Expected: `OK`

---

### Task 4: Moderator Agent with Delegation

**Files:**
- Create: `src/agents/moderator.py`

- [ ] **Step 1: Create src/agents/moderator.py**

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from src.models.itinerary import DiscussionEntry, Itinerary, PlanResult

from src.agents.guide import guide_agent
from src.agents.foodie import foodie_agent
from src.agents.local_expert import local_agent
from src.agents.finance import finance_agent


@dataclass
class TravelDeps:
    destination: str
    days: int
    budget: float
    interests: str


moderator_agent = Agent(
    "deepseek:deepseek-chat",
    deps_type=TravelDeps,
    result_type=PlanResult,
    instructions=(
        "You are a travel planning moderator. "
        "Your job is to gather expert opinions from your specialist team, "
        "then synthesize them into a complete travel itinerary.\n\n"
        "Team members available via tools:\n"
        "- plan_route: Guide - suggests attractions per day\n"
        "- plan_meals: Foodie - suggests meals per day\n"
        "- plan_local_tips: Local Expert - suggests hidden gems and tips\n"
        "- plan_budget: Finance Officer - allocates budget\n\n"
        "Call each specialist in order, passing them the context they need. "
        "After gathering all opinions, produce the final PlanResult with "
        "a complete Itinerary and a discussion log."
    ),
)


@moderator_agent.tool
async def plan_route(ctx: RunContext[TravelDeps]) -> list[str]:
    prompt = (
        f"Plan a {ctx.deps.days}-day trip to {ctx.deps.destination} "
        f"with budget {ctx.deps.budget} CNY. Interests: {ctx.deps.interests}."
    )
    result = await guide_agent.run(prompt, usage=ctx.usage)
    return result.output


@moderator_agent.tool
async def plan_meals(
    ctx: RunContext[TravelDeps], guide_suggestions: list[str]
) -> list[str]:
    prompt = (
        f"Plan meals for a {ctx.deps.days}-day trip to {ctx.deps.destination}. "
        f"Proposed itinerary: {guide_suggestions}"
    )
    result = await foodie_agent.run(prompt, usage=ctx.usage)
    return result.output


@moderator_agent.tool
async def plan_local_tips(
    ctx: RunContext[TravelDeps],
    guide_suggestions: list[str],
    meal_suggestions: list[str],
) -> list[str]:
    prompt = (
        f"Provide local tips for a trip to {ctx.deps.destination}. "
        f"Itinerary: {guide_suggestions}. "
        f"Meals: {meal_suggestions}."
    )
    result = await local_agent.run(prompt, usage=ctx.usage)
    return result.output


@moderator_agent.tool
async def plan_budget(
    ctx: RunContext[TravelDeps],
    guide_suggestions: list[str],
    meal_suggestions: list[str],
    local_tips: list[str],
) -> dict:
    prompt = (
        f"Allocate budget for a {ctx.deps.days}-day trip to {ctx.deps.destination} "
        f"with total budget {ctx.deps.budget} CNY. "
        f"Itinerary: {guide_suggestions}. "
        f"Meals: {meal_suggestions}. "
        f"Local tips: {local_tips}."
    )
    result = await finance_agent.run(prompt, usage=ctx.usage)
    return result.output


async def create_plan(destination: str, days: int, budget: float, interests: str) -> PlanResult:
    deps = TravelDeps(destination=destination, days=days, budget=budget, interests=interests)
    result = await moderator_agent.run(
        f"Plan a {days}-day trip to {destination}.",
        deps=deps,
    )
    return result.output
```

- [ ] **Step 2: Verify moderator imports**

Run: `cd /Users/shaohy/Github/easyPi && python -c "from src.agents.moderator import moderator_agent, create_plan; print('OK')"`
Expected: `OK`

---

### Task 5: FastAPI App with Routes

**Files:**
- Create: `src/web/__init__.py`
- Create: `src/web/routes.py`
- Create: `src/app.py`

- [ ] **Step 1: Create src/web/__init__.py** (empty)

- [ ] **Step 2: Create src/web/routes.py**

```python
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.agents.moderator import create_plan

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# In-memory store for plans (replace with DB in production)
plans: dict[str, dict] = {}


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/plan")
async def plan(
    request: Request,
    destination: str = Form(...),
    days: int = Form(...),
    budget: float = Form(...),
    interests: str = Form(""),
):
    plan_id = uuid.uuid4().hex[:8]
    result = await create_plan(destination, days, budget, interests)
    plans[plan_id] = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "result": result,
    }
    return templates.TemplateResponse("plan.html", {
        "request": request,
        "plan_id": plan_id,
        "result": result,
    })


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def view_plan(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Plan not found",
        })
    return templates.TemplateResponse("plan.html", {
        "request": request,
        "plan_id": plan_id,
        "result": plan_data["result"],
    })


@router.get("/dashboard/{plan_id}", response_class=HTMLResponse)
async def dashboard(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Plan not found",
        })
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "plan_id": plan_id,
        "result": plan_data["result"],
    })
```

- [ ] **Step 3: Create src/app.py**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.web.routes import router

app = FastAPI(title="Travel Assistant")
app.include_router(router)


def main():
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify app starts**

Run: `cd /Users/shaohy/Github/easyPi && python -c "from src.app import app; print('OK')"`
Expected: `OK`

---

### Task 6: Jinja2 Templates

**Files:**
- Create: `src/web/templates/base.html`
- Create: `src/web/templates/index.html`
- Create: `src/web/templates/plan.html`
- Create: `src/web/templates/dashboard.html`

- [ ] **Step 1: Create src/web/templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}旅游助手{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="bg-blue-600 text-white p-4 shadow">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <a href="/" class="text-xl font-bold">🌍 旅游助手</a>
        </div>
    </nav>
    <main class="max-w-6xl mx-auto p-6">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 2: Create src/web/templates/index.html**

```html
{% extends "base.html" %}
{% block title %}旅游助手 - 输入需求{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto bg-white rounded-xl shadow-md p-8 mt-8">
    <h1 class="text-2xl font-bold mb-6">规划你的旅行 ✈️</h1>
    <form action="/plan" method="post" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700">目的地</label>
            <input type="text" name="destination" required
                   class="mt-1 block w-full rounded-md border border-gray-300 p-2"
                   placeholder="例如：云南大理">
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700">天数</label>
            <input type="number" name="days" min="1" max="30" value="3" required
                   class="mt-1 block w-full rounded-md border border-gray-300 p-2">
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700">预算 (CNY)</label>
            <input type="number" name="budget" min="0" step="100" value="3000" required
                   class="mt-1 block w-full rounded-md border border-gray-300 p-2">
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700">偏好/备注</label>
            <textarea name="interests" rows="3"
                      class="mt-1 block w-full rounded-md border border-gray-300 p-2"
                      placeholder="例如：喜欢美食、自然风光，不想太累"></textarea>
        </div>
        <button type="submit"
                class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-medium">
            开始规划
        </button>
    </form>
    {% if error %}
    <div class="mt-4 p-3 bg-red-100 text-red-700 rounded">{{ error }}</div>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 3: Create src/web/templates/plan.html**

```html
{% extends "base.html" %}
{% block title %}旅行计划 - {{ result.itinerary.destination }}{% endblock %}
{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Discussion Log -->
    <div class="lg:col-span-1 bg-white rounded-xl shadow-md p-6">
        <h2 class="text-lg font-bold mb-4">💬 专家讨论过程</h2>
        <div class="space-y-3">
            {% for entry in result.discussion %}
            <div class="border-l-4 border-blue-500 pl-3">
                <div class="text-sm font-semibold text-blue-700">{{ entry.agent_name }}</div>
                <div class="text-sm text-gray-600 mt-1">{{ entry.content }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="mt-4">
            <a href="/dashboard/{{ plan_id }}"
               class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                📊 查看看板视图 →
            </a>
        </div>
    </div>

    <!-- Itinerary -->
    <div class="lg:col-span-2 space-y-4">
        <div class="bg-white rounded-xl shadow-md p-6">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h2 class="text-2xl font-bold">{{ result.itinerary.destination }}</h2>
                    <p class="text-gray-600">{{ result.itinerary.total_days }} 天行程</p>
                </div>
                <div class="text-right">
                    <span class="text-lg font-bold text-green-600">
                        ¥{{ "%.0f"|format(result.itinerary.total_budget) }}
                    </span>
                    <p class="text-sm text-gray-500">总预算</p>
                </div>
            </div>
            <p class="text-gray-700">{{ result.itinerary.summary }}</p>
        </div>

        {% for day in result.itinerary.daily_plans %}
        <div class="bg-white rounded-xl shadow-md p-6">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-lg font-bold">{{ day.date }}</h3>
                <span class="text-green-600 font-medium">¥{{ "%.0f"|format(day.budget) }}</span>
            </div>

            <div class="mb-3">
                <h4 class="text-sm font-semibold text-gray-600 mb-1">📍 景点</h4>
                <ul class="list-disc list-inside text-gray-700">
                    {% for attraction in day.attractions %}
                    <li>{{ attraction }}</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="mb-3">
                <h4 class="text-sm font-semibold text-gray-600 mb-1">🍽️ 美食</h4>
                <dl class="text-gray-700">
                    {% for meal, desc in day.meals.items() %}
                    <div class="flex gap-2">
                        <dt class="font-medium">{{ meal }}:</dt>
                        <dd>{{ desc }}</dd>
                    </div>
                    {% endfor %}
                </dl>
            </div>

            {% if day.tips %}
            <div>
                <h4 class="text-sm font-semibold text-gray-600 mb-1">💡 小贴士</h4>
                <ul class="list-disc list-inside text-gray-600 text-sm">
                    {% for tip in day.tips %}
                    <li>{{ tip }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Create src/web/templates/dashboard.html**

```html
{% extends "base.html" %}
{% block title %}看板 - {{ result.itinerary.destination }}{% endblock %}
{% block content %}
<!-- Summary Bar -->
<div class="bg-white rounded-xl shadow-md p-6 mb-6">
    <div class="grid grid-cols-4 gap-4 text-center">
        <div>
            <div class="text-2xl font-bold text-blue-600">{{ result.itinerary.destination }}</div>
            <div class="text-sm text-gray-500">目的地</div>
        </div>
        <div>
            <div class="text-2xl font-bold text-blue-600">{{ result.itinerary.total_days }}</div>
            <div class="text-sm text-gray-500">天数</div>
        </div>
        <div>
            <div class="text-2xl font-bold text-green-600">¥{{ "%.0f"|format(result.itinerary.total_budget) }}</div>
            <div class="text-sm text-gray-500">总预算</div>
        </div>
        <div>
            <div class="text-2xl font-bold text-purple-600">{{ result.discussion|length }}</div>
            <div class="text-sm text-gray-500">专家建议数</div>
        </div>
    </div>
    <div class="mt-4 text-center">
        <a href="/plan/{{ plan_id }}" class="text-blue-600 hover:text-blue-800 text-sm">
            📋 查看详细行程 →
        </a>
    </div>
</div>

<!-- Kanban-style Cards -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {% for day in result.itinerary.daily_plans %}
    <div class="bg-white rounded-xl shadow-md p-4 border-t-4 border-blue-500">
        <div class="flex justify-between items-center mb-3">
            <h3 class="font-bold">{{ day.date }}</h3>
            <span class="text-sm font-medium text-green-600">¥{{ "%.0f"|format(day.budget) }}</span>
        </div>
        <div class="space-y-2">
            <div>
                <h4 class="text-xs font-semibold text-gray-500 uppercase">景点</h4>
                <ul class="text-sm text-gray-700 list-disc list-inside">
                    {% for a in day.attractions[:3] %}
                    <li>{{ a }}</li>
                    {% endfor %}
                    {% if day.attractions|length > 3 %}
                    <li class="text-blue-500">+{{ day.attractions|length - 3 }} 更多...</li>
                    {% endif %}
                </ul>
            </div>
            <div>
                <h4 class="text-xs font-semibold text-gray-500 uppercase">美食</h4>
                <div class="text-sm text-gray-700">
                    {% for meal, desc in day.meals.items() %}
                    <div>{{ meal }}: {{ desc[:30] }}{% if desc|length > 30 %}...{% endif %}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Discussion Panel -->
<div class="mt-6 bg-white rounded-xl shadow-md p-6">
    <h2 class="text-lg font-bold mb-4">💬 完整讨论记录</h2>
    <div class="space-y-4 max-h-96 overflow-y-auto">
        {% for entry in result.discussion %}
        <div class="border-l-4 border-gray-300 pl-4 py-2">
            <div class="font-semibold text-blue-700">{{ entry.agent_name }}</div>
            <div class="text-gray-600 mt-1 whitespace-pre-wrap">{{ entry.content }}</div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

### Task 7: Integration Test and Smoke Test

**Files:**
- Create: `tests/test_models.py`

- [ ] **Step 1: Create tests/test_models.py**

```python
from src.models.itinerary import Itinerary, DailyPlan, PlanResult, DiscussionEntry


def test_daily_plan_creation():
    plan = DailyPlan(
        day=1, date="Day 1",
        attractions=["Great Wall"],
        meals={"lunch": "Peking Duck"},
        budget=500.0, tips=["Bring water"]
    )
    assert plan.day == 1
    assert "Great Wall" in plan.attractions


def test_itinerary_creation():
    itinerary = Itinerary(
        destination="Beijing", total_days=1, total_budget=500.0,
        daily_plans=[], summary="Great trip"
    )
    assert itinerary.destination == "Beijing"
    assert itinerary.total_days == 1
```

- [ ] **Step 2: Run tests**

Run: `cd /Users/shaohy/Github/easyPi && python -m pytest tests/test_models.py -v`
Expected: 2 passed

---

### Task 8: Run Application and Verify

- [ ] **Step 1: Start the application**

Run: `cd /Users/shaohy/Github/easyPi && python src/app.py`
Expected: Uvicorn running on http://127.0.0.1:8000

- [ ] **Step 2: Open browser and test**

Open: http://127.0.0.1:8000
Expected: Form visible, can submit a trip request

- [ ] **Step 3: Submit a test plan**

Fill form: destination="云南大理", days=3, budget=3000, interests="美食+自然风光"
Expected: Plan page shows discussion log and itinerary

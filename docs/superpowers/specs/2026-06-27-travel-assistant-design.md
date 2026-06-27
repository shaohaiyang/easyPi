# Travel Assistant - Multi-Agent Design

## Overview

A multi-agent travel assistant built with pydantic-ai, using a moderator-led discussion pattern with 4 specialist agents. DeepSeek as the main model, GLM for specialist agents. Web dashboard with FastAPI + Jinja2.

## Architecture

```
User Input (destination, days, budget, preferences)
        │
        ▼
┌─────────────────────────┐
│     Moderator Agent     │  model: deepseek:deepseek-chat
│  (orchestrates discussion)
└──────────┬──────────────┘
           │ agent delegation (sequential)
     ┌─────┼─────┬─────┐
     ▼     ▼     ▼     ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│ Guide  ││ Foodie ││ Local  ││Finance │  model: OpenAIChatModel
│导游    ││美食家  ││本地通  ││财务官  │  (GLM OpenAI-compatible)
└────────┘└────────┘└────────┘└────────┘
           │
           ▼
┌─────────────────────────┐
│  Structured Itinerary   │  Pydantic output model
│  (day-by-day plan)      │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│  FastAPI + Jinja2 UI    │
│  discussion log + plan  │
└─────────────────────────┘
```

## Agents

### Moderator Agent
- **Model**: `deepseek:deepseek-chat`
- **Role**: Receives user requirements, calls each specialist via `@agent.tool`, synthesizes final output
- **Deps**: Shared HTTP client, user preferences

### Guide Agent (导游)
- **Model**: GLM via `OpenAIChatModel(base_url="https://open.bigmodel.cn/api/paas/v4")`
- **Role**: Route planning, attractions, daily itinerary structure
- **Output**: Suggested attractions per day, routing logic

### Foodie Agent (美食家)
- **Model**: GLM
- **Role**: Restaurant recommendations, local cuisine, food streets
- **Output**: Meals per day, budget dining options

### Local Expert Agent (本地通)
- **Model**: GLM
- **Role**: Hidden gems, cultural tips, transportation, weather advice
- **Output**: Local insights, transport recommendations

### Finance Officer Agent (财务官)
- **Model**: GLM
- **Role**: Budget allocation, cost estimates, money-saving tips
- **Output**: Daily budget breakdown, total cost estimate

## Data Flow

1. User submits trip requirements via web form (destination, dates, budget, interests)
2. Moderator receives the brief, stores in `RunContext.deps`
3. Moderator calls each specialist sequentially via tools, passing context:
   - Guide → produces daily route
   - Foodie → adds food recommendations per day
   - Local Expert → adds cultural/transport tips
   - Finance Officer → assigns budget to each item
4. Each specialist receives previous specialists' outputs for context
5. Moderator synthesizes all inputs into a structured Itinerary model
6. Result rendered in FastAPI + Jinja2 dashboard

## Output Structure (Pydantic Models)

```python
class DailyPlan(BaseModel):
    day: int
    date: str
    attractions: list[str]
    meals: dict[str, str]       # breakfast/lunch/dinner
    budget: float
    tips: list[str]

class Itinerary(BaseModel):
    destination: str
    total_days: int
    total_budget: float
    daily_plans: list[DailyPlan]
    summary: str
```

## Discussion Log

Each specialist's full response is stored in a discussion log, displayed on the Web UI alongside the final itinerary for transparency.

## Web UI (FastAPI + Jinja2)

### Routes
- `GET /` — Main form for trip input
- `POST /plan` — Submit request, triggers agent workflow (SSE streaming for progress)
- `GET /plan/{id}` — View discussion log + final itinerary
- `GET /plan/{id}/dashboard` — Dashboard view with kanban-style layout

### Layout
- Left panel: Discussion thread (each agent's card)
- Right panel: Final itinerary (day-by-day accordion)
- Top: Summary bar (destination, days, total budget)

## Project Structure

```
easyPi/
├── pyproject.toml
├── .env                          # API keys
├── src/
│   ├── app.py                    # FastAPI entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── moderator.py          # Moderator agent
│   │   ├── guide.py              # Guide agent
│   │   ├── foodie.py             # Foodie agent
│   │   ├── local_expert.py       # Local expert agent
│   │   └── finance.py            # Finance officer agent
│   ├── models/
│   │   ├── __init__.py
│   │   └── itinerary.py          # Pydantic output models
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py             # FastAPI routes
│   │   └── templates/
│   │       ├── base.html
│   │       ├── index.html        # Input form
│   │       ├── plan.html         # Discussion log + final plan
│   │       └── dashboard.html    # Kanban dashboard
│   └── config.py                 # Model config (DeepSeek / GLM)
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-27-travel-assistant-design.md
```

## Implementation Order

1. Project scaffold (pyproject.toml, deps, config)
2. Pydantic output models
3. Specialist agents (guide, foodie, local, finance)
4. Moderator agent with delegation logic
5. FastAPI routes + SSE streaming
6. Jinja2 templates (form, plan, dashboard)
7. Integration test

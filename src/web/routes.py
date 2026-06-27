import uuid
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from src.agents.moderator import create_plan

router = APIRouter()

TEMPLATE_DIR = str(Path(__file__).parent / "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), auto_reload=True)

plans: dict[str, dict] = {}


def render(name: str, **context) -> str:
    template = env.get_template(name)
    return template.render(**context)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = render("index.html", request=request)
    return HTMLResponse(html)


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
    html = render("plan.html", request=request, plan_id=plan_id, result=result)
    return HTMLResponse(html)


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def view_plan(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        html = render("index.html", request=request, error="Plan not found")
        return HTMLResponse(html)
    html = render(
        "plan.html",
        request=request,
        plan_id=plan_id,
        result=plan_data["result"],
    )
    return HTMLResponse(html)


@router.get("/dashboard/{plan_id}", response_class=HTMLResponse)
async def dashboard(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        html = render("index.html", request=request, error="Plan not found")
        return HTMLResponse(html)
    html = render(
        "dashboard.html",
        request=request,
        plan_id=plan_id,
        result=plan_data["result"],
    )
    return HTMLResponse(html)

import uuid
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.agents.moderator import create_plan

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

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
    return templates.TemplateResponse(
        "plan.html",
        {"request": request, "plan_id": plan_id, "result": result},
    )


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def view_plan(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": "Plan not found"}
        )
    return templates.TemplateResponse(
        "plan.html",
        {
            "request": request,
            "plan_id": plan_id,
            "result": plan_data["result"],
        },
    )


@router.get("/dashboard/{plan_id}", response_class=HTMLResponse)
async def dashboard(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": "Plan not found"}
        )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "plan_id": plan_id,
            "result": plan_data["result"],
        },
    )

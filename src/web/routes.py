import asyncio
import json
import uuid
from pathlib import Path

import markdown as md_lib
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader

from src.agents.moderator import create_plan
from src.progress import get_tracker

router = APIRouter()

TEMPLATE_DIR = str(Path(__file__).parent / "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), auto_reload=True)


def render_markdown(text: str) -> str:
    return md_lib.markdown(text, extensions=["fenced_code", "tables", "nl2br"])


env.filters["markdown"] = render_markdown

plans: dict[str, dict] = {}
_background_tasks: set[asyncio.Task] = set()


def render(name: str, **context) -> str:
    template = env.get_template(name)
    return template.render(**context)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = render("index.html", request=request)
    return HTMLResponse(html)


@router.post("/plan")
async def start_plan(
    request: Request,
    destination: str = Form(...),
    days: int = Form(...),
    budget: float = Form(...),
    interests: str = Form(""),
    language: str = Form("zh"),
):
    plan_id = uuid.uuid4().hex[:8]

    task = asyncio.create_task(
        _run_plan(plan_id, destination, days, budget, interests, language)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    html = render(
        "progress.html",
        request=request,
        plan_id=plan_id,
        destination=destination,
        days=days,
        budget=budget,
        interests=interests,
    )
    return HTMLResponse(html)


async def _run_plan(
    plan_id: str, destination: str, days: int, budget: float, interests: str,
    language: str = "zh",
):
    tracker = get_tracker(plan_id)
    result = await create_plan(destination, days, budget, interests, tracker, language)
    plans[plan_id] = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "language": language,
        "result": result,
    }


@router.get("/plan/{plan_id}/progress")
async def plan_progress(request: Request, plan_id: str):
    tracker = get_tracker(plan_id)

    async def event_generator():
        # 不设总超时，改为"无进度空闲超时"：600 秒无任何进度事件则判定超时
        # 每次 tracker._event 被 set 都会重置这个计时器
        while not tracker.done:
            try:
                await asyncio.wait_for(tracker._event.wait(), timeout=600)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'failed': True, 'error': 'LLM 响应超时（600 秒无响应），请重试'})}\n\n"
                return

            tracker._event.clear()

            if tracker.failed:
                yield f"data: {json.dumps({'failed': True, 'error': tracker.error})}\n\n"
                return

            data = json.dumps(
                {
                    "stage": tracker.current_stage,
                    "message": tracker.message,
                    "pct": tracker.pct,
                    "done": False,
                }
            )
            yield f"data: {data}\n\n"

        data = json.dumps({"done": True, "plan_id": plan_id})
        yield f"data: {data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def view_plan(request: Request, plan_id: str):
    plan_data = plans.get(plan_id)
    if not plan_data:
        html = render("index.html", request=request, error="规划未找到，请重新提交")
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
        html = render("index.html", request=request, error="规划未找到，请重新提交")
        return HTMLResponse(html)
    html = render(
        "dashboard.html",
        request=request,
        plan_id=plan_id,
        result=plan_data["result"],
    )
    return HTMLResponse(html)

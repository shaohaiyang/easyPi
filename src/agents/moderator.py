import asyncio

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, MODEL_NAME, VOLC_BASE_URL
from src.models.itinerary import DailyPlan, DiscussionEntry, Itinerary, PlanResult
from src.progress import ProgressTracker

from src.agents.guide import create_guide_agent
from src.agents.foodie import create_foodie_agent
from src.agents.local_expert import create_local_agent
from src.agents.finance import create_finance_agent


SOOTHING_MESSAGES = [
    "好的规划值得耐心等待 ✨",
    "几位旅行专家正在热烈讨论中…",
    "深呼吸，美好的旅程即将呈现 🌿",
    "导游正在翻阅当地攻略…",
    "美食家正在流连于各大食肆之间 😋",
]


MODERATOR_INSTRUCTIONS = {
    "zh": "你是旅行规划主持人。用2-3段总结最终旅行计划，包括每日行程概览。请用中文回答。",
    "en": "You are a travel planning moderator. Summarize the final travel plan in 2-3 paragraphs. Include a brief day-by-day overview.",
}


async def create_plan(
    destination: str,
    days: int,
    budget: float,
    interests: str,
    tracker: ProgressTracker | None = None,
    language: str = "zh",
) -> PlanResult:
    try:
        return await _run_plan(destination, days, budget, interests, tracker, language)
    except Exception as e:
        if tracker:
            tracker.mark_failed(str(e))
        raise


async def _run_agent_with_retry(
    agent: Agent,
    prompt: str,
    tracker: ProgressTracker | None = None,
    stage: str = "",
    heartbeat_msg: str = "",
    max_retries: int = 3,
):
    last_exception: Exception | None = None
    for attempt in range(1, max_retries + 1):
        heartbeat_task: asyncio.Task | None = None
        try:
            if tracker:
                async def _heartbeat():
                    while True:
                        await asyncio.sleep(30)
                        tracker.update(stage, heartbeat_msg, tracker.pct)

                heartbeat_task = asyncio.create_task(_heartbeat())

            result = await agent.run(prompt)
            return result

        except (httpx.TimeoutException, httpx.HTTPStatusError, TimeoutError) as e:
            last_exception = e
            if attempt < max_retries:
                wait = 5 * (2 ** (attempt - 1))
                if tracker:
                    tracker.update(stage, f"⏳ 请求超时，{wait}秒后重试（第{attempt}次）...", tracker.pct)
                await asyncio.sleep(wait)
        finally:
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    raise last_exception or RuntimeError("Agent run failed after retries")


def _parse_daily_plans(
    guide_output: str,
    foodie_output: str,
    local_output: str,
    finance_output: str,
) -> list[DailyPlan]:
    import re
    days: list[DailyPlan] = []

    sep = r'(?=Day\s*\d+\s*[:：])'
    guide_days = re.split(sep, guide_output.strip())
    foodie_days = re.split(sep, foodie_output.strip())
    finance_days = re.split(sep, finance_output.strip())

    guide_parsed = {}
    for block in guide_days:
        m = re.match(r'Day\s*(\d+)\s*[:：](.*)', block, re.DOTALL)
        if m:
            guide_parsed[int(m.group(1))] = m.group(2).strip()

    foodie_parsed = {}
    for block in foodie_days:
        m = re.match(r'Day\s*(\d+)\s*[:：](.*)', block, re.DOTALL)
        if m:
            foodie_parsed[int(m.group(1))] = m.group(2).strip()

    finance_parsed = {}
    for block in finance_days:
        m = re.match(r'Day\s*(\d+)\s*[:：](.*)', block, re.DOTALL)
        if m:
            finance_parsed[int(m.group(1))] = m.group(2).strip()

    local_items = [line.strip() for line in local_output.strip().split('\n') if line.strip()]
    local_tips = []
    for item in local_items:
        item_clean = re.sub(r'^\d+[\.、）\)]\s*', '', item).strip()
        if item_clean and len(item_clean) > 5:
            local_tips.append(item_clean)

    all_day_nums = set(guide_parsed) | set(foodie_parsed) | set(finance_parsed)
    max_days = max(all_day_nums) if all_day_nums else 3

    for i in range(1, max_days + 1):
        desc = guide_parsed.get(i, '')
        if desc:
            parts = [a.strip().rstrip('，,') for a in re.split(r'[；;]\s*|→|，\s*(?=[\u4e00-\u9fff])', desc) if a.strip()]
            attractions = [p for p in parts if len(p) > 2][:8]
        else:
            attractions = [f"第{i}天的行程安排"]

        meals: dict[str, str] = {}
        desc = foodie_parsed.get(i, '')
        if desc:
            for meal_type in ['早餐', '午餐', '晚餐']:
                m = re.search(rf'{re.escape(meal_type)}[:：]?(.*?)(?=早餐|午餐|晚餐|$)', desc)
                if m:
                    val = m.group(1).strip().rstrip('；;，,')
                    if val:
                        meals[meal_type] = val[:100]
        if not meals:
            meals['推荐'] = '品尝当地特色美食'

        day_tips = []
        per_day = max(1, len(local_tips) // max_days)
        start = (i - 1) * per_day
        day_tips = local_tips[start:start + per_day]

        day_budget = 0.0
        desc = finance_parsed.get(i, '')
        if desc:
            nums = re.findall(r'(\d+(?:\.\d+)?)', desc)
            if nums:
                day_budget = float(nums[0])

        days.append(DailyPlan(
            day=i,
            date=f"Day {i}",
            attractions=attractions,
            meals=meals,
            budget=day_budget,
            tips=day_tips,
        ))

    return days


async def _run_plan(
    destination: str,
    days: int,
    budget: float,
    interests: str,
    tracker: ProgressTracker | None = None,
    language: str = "zh",
) -> PlanResult:
    guide_agent = create_guide_agent(language)
    foodie_agent = create_foodie_agent(language)
    local_agent = create_local_agent(language)
    finance_agent = create_finance_agent(language)

    if language == "zh":
        if tracker:
            tracker.update("guide", f"🌏 导游正在规划 {destination} 的最佳路线…", 10)
        guide_prompt = f"为{destination}规划{days}天的行程，预算为{budget}元。兴趣：{interests}。"
        guide_heartbeat = "🌏 导游正在思考中…"
    else:
        if tracker:
            tracker.update("guide", f"🌏 Guide is planning the best route for {destination}…", 10)
        guide_prompt = f"Plan a {days}-day trip to {destination} with budget {budget} CNY. Interests: {interests}."
        guide_heartbeat = "🌏 Guide is thinking…"

    guide_result = await _run_agent_with_retry(
        guide_agent, guide_prompt, tracker, "guide", guide_heartbeat
    )
    guide_output = guide_result.output

    if language == "zh":
        if tracker:
            tracker.add_stage_result("导游", guide_output)
            tracker.update("foodie", "🍜 美食家正在搜寻当地特色美食…", 30)
            tracker.update("foodie", f"🍜 美食家说：{SOOTHING_MESSAGES[2]}", 35)
        foodie_prompt = f"为{destination}的{days}天行程规划美食。拟议行程：{guide_output}"
        foodie_heartbeat = "🍜 美食家正在思考中…"
    else:
        if tracker:
            tracker.add_stage_result("Guide", guide_output)
            tracker.update("foodie", "🍜 Foodie is searching for local delicacies…", 30)
            tracker.update("foodie", f"🍜 {SOOTHING_MESSAGES[2].replace('美食家正在流连于各大食肆之间', 'Foodie is exploring')}", 35)
        foodie_prompt = f"Plan meals for a {days}-day trip to {destination}. Proposed itinerary: {guide_output}"
        foodie_heartbeat = "🍜 Foodie is thinking…"

    foodie_result = await _run_agent_with_retry(
        foodie_agent, foodie_prompt, tracker, "foodie", foodie_heartbeat
    )
    foodie_output = foodie_result.output

    if language == "zh":
        if tracker:
            tracker.add_stage_result("美食家", foodie_output)
            tracker.update("local", "🏘️ 本地通正在挖掘小众宝藏景点…", 50)
        local_prompt = f"为{destination}的行程提供本地贴士。行程：{guide_output}。美食：{foodie_output}。"
        local_heartbeat = "🏘️ 本地通正在思考中…"
    else:
        if tracker:
            tracker.add_stage_result("Foodie", foodie_output)
            tracker.update("local", "🏘️ Local expert is finding hidden gems…", 50)
        local_prompt = f"Provide local tips for a trip to {destination}. Itinerary: {guide_output}. Meals: {foodie_output}."
        local_heartbeat = "🏘️ Local expert is thinking…"

    local_result = await _run_agent_with_retry(
        local_agent, local_prompt, tracker, "local", local_heartbeat
    )
    local_output = local_result.output

    if language == "zh":
        if tracker:
            tracker.add_stage_result("本地通", local_output)
            tracker.update("finance", "💰 财务官正在精打细算…", 70)
        finance_prompt = (
            f"为{destination}的{days}天行程分配预算，总预算{budget}元。"
            f"行程：{guide_output}。美食：{foodie_output}。本地贴士：{local_output}。"
        )
        finance_heartbeat = "💰 财务官正在思考中…"
    else:
        if tracker:
            tracker.add_stage_result("Local Expert", local_output)
            tracker.update("finance", "💰 Finance officer is calculating…", 70)
        finance_prompt = (
            f"Allocate budget for a {days}-day trip to {destination} "
            f"with total budget {budget} CNY. "
            f"Itinerary: {guide_output}. "
            f"Meals: {foodie_output}. "
            f"Local tips: {local_output}."
        )
        finance_heartbeat = "💰 Finance officer is thinking…"

    finance_result = await _run_agent_with_retry(
        finance_agent, finance_prompt, tracker, "finance", finance_heartbeat
    )
    finance_output = finance_result.output

    if language == "zh":
        if tracker:
            tracker.add_stage_result("财务官", finance_output)
            tracker.update("synthesizing", "🧠 主持人正在综合所有专家建议…", 85)
            tracker.update("synthesizing", f"🧠 {SOOTHING_MESSAGES[0]}", 90)
        synthesis_prompt = (
            f"综合整理一份{days}天的{destination}行程"
            f"（预算：{budget}元，兴趣：{interests}）。\n\n"
            f"## 导游建议\n{guide_output}\n\n"
            f"## 美食建议\n{foodie_output}\n\n"
            f"## 本地贴士\n{local_output}\n\n"
            f"## 预算\n{finance_output}"
        )
    else:
        if tracker:
            tracker.add_stage_result("Finance Officer", finance_output)
            tracker.update("synthesizing", "🧠 Moderator is synthesizing all expert advice…", 85)
            tracker.update("synthesizing", f"🧠 {SOOTHING_MESSAGES[0]}", 90)
        synthesis_prompt = (
            f"Synthesize a {days}-day trip to {destination} "
            f"(budget: {budget} CNY, interests: {interests}).\n\n"
            f"## Guide suggestions\n{guide_output}\n\n"
            f"## Food suggestions\n{foodie_output}\n\n"
            f"## Local tips\n{local_output}\n\n"
            f"## Budget\n{finance_output}"
        )

    moderator_model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )

    moderator_agent = Agent(
        moderator_model,
        instructions=MODERATOR_INSTRUCTIONS[language],
    )

    final = await _run_agent_with_retry(
        moderator_agent, synthesis_prompt, tracker, "synthesizing", "🧠 主持人正在思考中…" if language == "zh" else "🧠 Moderator is thinking…"
    )

    if language == "zh":
        names = ["导游", "美食家", "本地通", "财务官"]
    else:
        names = ["Guide", "Foodie", "Local Expert", "Finance Officer"]

    daily_plans = _parse_daily_plans(guide_output, foodie_output, local_output, finance_output)
    discussion = [
        DiscussionEntry(agent_name=names[0], content=guide_output),
        DiscussionEntry(agent_name=names[1], content=foodie_output),
        DiscussionEntry(agent_name=names[2], content=local_output),
        DiscussionEntry(agent_name=names[3], content=finance_output),
    ]
    plan = PlanResult(
        itinerary=Itinerary(
            destination=destination,
            total_days=days,
            total_budget=budget,
            daily_plans=daily_plans,
            summary=final.output,
        ),
        discussion=discussion,
    )

    if language == "zh":
        done_msg = "✅ 行程规划完成！"
        tracker_name = "主持人"
    else:
        done_msg = "✅ Plan complete!"
        tracker_name = "Moderator"

    if tracker:
        tracker.add_stage_result(tracker_name, plan.itinerary.summary)
        tracker.update("done", done_msg, 100)
        tracker.done = True
        tracker.result = plan

    return plan

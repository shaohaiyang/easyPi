from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, DEEPSEEK_MODEL, GLM_MODEL_NAME, VOLC_BASE_URL
from src.models.itinerary import DiscussionEntry, Itinerary, PlanResult
from src.progress import ProgressTracker

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


SOOTHING_MESSAGES = [
    "好的规划值得耐心等待 ✨",
    "几位旅行专家正在热烈讨论中…",
    "深呼吸，美好的旅程即将呈现 🌿",
    "导游正在翻阅当地攻略…",
    "美食家正在流连于各大食肆之间 😋",
]


async def create_plan(
    destination: str,
    days: int,
    budget: float,
    interests: str,
    tracker: ProgressTracker | None = None,
) -> PlanResult:
    try:
        return await _run_plan(destination, days, budget, interests, tracker)
    except Exception as e:
        if tracker:
            tracker.mark_failed(str(e))
        raise


async def _run_plan(
    destination: str,
    days: int,
    budget: float,
    interests: str,
    tracker: ProgressTracker | None = None,
) -> PlanResult:
    if tracker:
        tracker.update("guide", f"🌏 导游正在规划 {destination} 的最佳路线…", 10)

    guide_prompt = (
        f"Plan a {days}-day trip to {destination} "
        f"with budget {budget} CNY. Interests: {interests}."
    )
    guide_result = await guide_agent.run(guide_prompt)
    guide_output = guide_result.output

    if tracker:
        tracker.add_stage_result("导游", guide_output)
        tracker.update("foodie", "🍜 美食家正在搜寻当地特色美食…", 30)
        tracker.update("foodie", f"🍜 美食家说：{SOOTHING_MESSAGES[2]}", 35)

    foodie_prompt = (
        f"Plan meals for a {days}-day trip to {destination}. "
        f"Proposed itinerary: {guide_output}"
    )
    foodie_result = await foodie_agent.run(foodie_prompt)
    foodie_output = foodie_result.output

    if tracker:
        tracker.add_stage_result("美食家", foodie_output)
        tracker.update("local", "🏘️ 本地通正在挖掘小众宝藏景点…", 50)

    local_prompt = (
        f"Provide local tips for a trip to {destination}. "
        f"Itinerary: {guide_output}. Meals: {foodie_output}."
    )
    local_result = await local_agent.run(local_prompt)
    local_output = local_result.output

    if tracker:
        tracker.add_stage_result("本地通", local_output)
        tracker.update("finance", "💰 财务官正在精打细算…", 70)

    finance_prompt = (
        f"Allocate budget for a {days}-day trip to {destination} "
        f"with total budget {budget} CNY. "
        f"Itinerary: {guide_output}. "
        f"Meals: {foodie_output}. "
        f"Local tips: {local_output}."
    )
    finance_result = await finance_agent.run(finance_prompt)
    finance_output = finance_result.output

    if tracker:
        tracker.add_stage_result("财务官", finance_output)
        tracker.update("synthesizing", "🧠 主持人正在综合所有专家建议…", 85)
        tracker.update("synthesizing", f"🧠 {SOOTHING_MESSAGES[0]}", 90)

    moderator_model = OpenAIChatModel(
        DEEPSEEK_MODEL,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )

    moderator_agent = Agent(
        moderator_model,
        output_type=PlanResult,
        instructions=(
            "You are a travel planning moderator. "
            "Synthesize the expert opinions below into a complete travel itinerary.\n\n"
            "Return a PlanResult with a structured Itinerary and a discussion log "
            "containing each expert's contribution."
        ),
    )

    synthesis_prompt = (
        f"Synthesize a {days}-day trip to {destination} "
        f"(budget: {budget} CNY, interests: {interests}).\n\n"
        f"## Guide suggestions\n{guide_output}\n\n"
        f"## Food suggestions\n{foodie_output}\n\n"
        f"## Local tips\n{local_output}\n\n"
        f"## Budget\n{finance_output}"
    )
    final = await moderator_agent.run(synthesis_prompt)

    plan = final.output
    if not plan.discussion:
        discussion = [
            DiscussionEntry(agent_name="导游", content=str(guide_output)),
            DiscussionEntry(agent_name="美食家", content=str(foodie_output)),
            DiscussionEntry(agent_name="本地通", content=str(local_output)),
            DiscussionEntry(agent_name="财务官", content=str(finance_output)),
        ]
        plan.discussion = discussion

    if tracker:
        tracker.add_stage_result("主持人", str(plan))
        tracker.update("done", "✅ 行程规划完成！", 100)
        tracker.done = True
        tracker.result = plan

    return plan

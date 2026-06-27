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
    output_type=PlanResult,
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


async def create_plan(
    destination: str, days: int, budget: float, interests: str
) -> PlanResult:
    deps = TravelDeps(
        destination=destination, days=days, budget=budget, interests=interests
    )
    result = await moderator_agent.run(
        f"Plan a {days}-day trip to {destination}.",
        deps=deps,
    )
    return result.output

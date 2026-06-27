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

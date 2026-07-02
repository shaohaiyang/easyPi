from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, MODEL_NAME, VOLC_BASE_URL


INSTRUCTIONS = {
    "zh": (
        "你是旅行财务官。根据目的地、行程天数和预算约束，为每天分配预算，包括："
        "交通、餐饮、景点门票、住宿、杂项。每天预算以'Day N:'开头单独一行输出。"
        "最后给出总预算估算和省钱建议。请用中文回答。"
    ),
    "en": (
        "You are a travel finance officer. "
        "Based on the destination, duration, itinerary, and budget constraints, "
        "allocate budget for each day including: "
        "transportation, meals, attractions tickets, accommodation, miscellaneous. "
        "Output each day's budget as a separate line starting with 'Day N:'. "
        "Include total estimated cost and money-saving tips at the end."
    ),
}


def create_finance_agent(language: str = "zh") -> Agent:
    model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(model, instructions=INSTRUCTIONS[language])


finance_agent = create_finance_agent()

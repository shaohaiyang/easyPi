from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, MODEL_NAME, VOLC_BASE_URL


INSTRUCTIONS = {
    "zh": (
        "你是本地美食专家。根据用户的目的地、旅行天数和拟议行程，为每天推荐早餐、午餐和晚餐选项。"
        "每天以'Day N:'开头，后跟当日的美食推荐。包括当地特色菜和性价比高的选择。请用中文回答。"
    ),
    "en": (
        "You are a local food expert. "
        "Based on the user's destination, trip duration, and the proposed itinerary, "
        "suggest breakfast, lunch, and dinner options for each day. "
        "Output each day as a separate line starting with 'Day N:', "
        "followed by the meal recommendations for that day. "
        "Include local specialties and budget-friendly options."
    ),
}


def create_foodie_agent(language: str = "zh") -> Agent:
    model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(model, instructions=INSTRUCTIONS[language])


foodie_agent = create_foodie_agent()

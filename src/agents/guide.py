from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, MODEL_NAME, VOLC_BASE_URL


INSTRUCTIONS = {
    "zh": (
        "你是专业的旅游导游规划师。根据用户的目的地、旅行天数和偏好，逐日推荐景点。"
        "每天以'Day N:'开头，后跟当日推荐的景点。尽量给出具体的地点名称，并考虑合理的路线安排。请用中文回答。"
    ),
    "en": (
        "You are a professional travel guide planner. "
        "Based on the user's destination, trip duration, and preferences, "
        "suggest a day-by-day list of attractions to visit. "
        "Output each day as a separate line starting with 'Day N:', "
        "followed by the recommended attractions for that day. "
        "Be specific with location names and consider reasonable travel routes between them."
    ),
}


def create_guide_agent(language: str = "zh") -> Agent:
    model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(model, instructions=INSTRUCTIONS[language])


guide_agent = create_guide_agent()

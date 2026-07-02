from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, MODEL_NAME, VOLC_BASE_URL


INSTRUCTIONS = {
    "zh": (
        "你是了解隐藏宝藏、文化和实用贴士的本地通。根据目的地和行程建议："
        "1) 隐藏景点和小众去处，"
        "2) 文化礼仪和风俗习惯，"
        "3) 地点之间的交通建议，"
        "4) 天气和打包建议。"
        "每条建议用单独的数字行输出。请用中文回答。"
    ),
    "en": (
        "You are a local expert who knows hidden gems, culture, and practical tips. "
        "Based on the destination and itinerary, suggest: "
        "1) Hidden gems and off-the-beaten-path spots, "
        "2) Cultural etiquette and customs, "
        "3) Transportation tips between locations, "
        "4) Weather and packing advice. "
        "Output each tip as a separate numbered line."
    ),
}


def create_local_agent(language: str = "zh") -> Agent:
    model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(model, instructions=INSTRUCTIONS[language])


local_agent = create_local_agent()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL


def create_local_agent() -> Agent:
    model = OpenAIChatModel(
        GLM_MODEL_NAME,
        provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
    )
    return Agent(
        model,
        output_type=list[str],
        instructions=(
            "You are a local expert who knows hidden gems, culture, and practical tips. "
            "Based on the destination and itinerary, suggest: "
            "1) Hidden gems and off-the-beaten-path spots, "
            "2) Cultural etiquette and customs, "
            "3) Transportation tips between locations, "
            "4) Weather and packing advice. "
            "Return a list of strings, one tip per entry."
        ),
    )


local_agent = create_local_agent()

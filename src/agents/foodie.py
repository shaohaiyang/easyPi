from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, GLM_MODEL_NAME, VOLC_BASE_URL


def create_foodie_agent() -> Agent:
    model = OpenAIChatModel(
        GLM_MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(
        model,
        output_type=list[str],
        instructions=(
            "You are a local food expert. "
            "Based on the user's destination, trip duration, and the proposed itinerary, "
            "suggest breakfast, lunch, and dinner options for each day. "
            "Return a list of strings, each describing one day's meal recommendations. "
            "Include local specialties and budget-friendly options."
        ),
    )


foodie_agent = create_foodie_agent()

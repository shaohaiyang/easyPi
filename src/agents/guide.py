from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import GLM_API_KEY, GLM_MODEL_NAME, GLM_BASE_URL


def create_guide_agent() -> Agent:
    model = OpenAIChatModel(
        GLM_MODEL_NAME,
        provider=OpenAIProvider(base_url=GLM_BASE_URL, api_key=GLM_API_KEY),
    )
    return Agent(
        model,
        output_type=list[str],
        instructions=(
            "You are a professional travel guide planner. "
            "Based on the user's destination, trip duration, and preferences, "
            "suggest a day-by-day list of attractions to visit. "
            "Return a list of strings, each describing one day's recommended attractions. "
            "Be specific with location names and consider reasonable travel routes between them."
        ),
    )


guide_agent = create_guide_agent()

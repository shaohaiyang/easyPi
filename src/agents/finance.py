from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.config import VOLC_API_KEY, GLM_MODEL_NAME, VOLC_BASE_URL


def create_finance_agent() -> Agent:
    model = OpenAIChatModel(
        GLM_MODEL_NAME,
        provider=OpenAIProvider(base_url=VOLC_BASE_URL, api_key=VOLC_API_KEY),
    )
    return Agent(
        model,
        output_type=dict,
        instructions=(
            "You are a travel finance officer. "
            "Based on the destination, duration, itinerary, and budget constraints, "
            "allocate budget for each day including: "
            "transportation, meals, attractions tickets, accommodation, miscellaneous. "
            "Return a dict with keys as day labels and values as budget breakdown strings. "
            "Provide total estimated cost and money-saving tips."
        ),
    )


finance_agent = create_finance_agent()

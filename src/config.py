import os
from dotenv import load_dotenv

load_dotenv()

VOLC_API_KEY = os.getenv("VOLC_API_KEY") or "placeholder-volc-key"
VOLC_BASE_URL = os.getenv(
    "VOLC_BASE_URL",
    "https://ark.cn-beijing.volces.com/api/coding/v3",
)

MODEL_NAME = os.getenv("MODEL_NAME") or "deepseek-v4-flash-260425"

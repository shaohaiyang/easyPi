import os
from dotenv import load_dotenv

load_dotenv()

VOLC_API_KEY = os.getenv("VOLC_API_KEY") or "placeholder-volc-key"
VOLC_BASE_URL = os.getenv(
    "VOLC_BASE_URL",
    "https://ark.cn-beijing.volces.com/api/coding/v3",
)

DEEPSEEK_MODEL = "deepseek-v4-flash-260425"
GLM_MODEL_NAME = "glm-4-7-251222"

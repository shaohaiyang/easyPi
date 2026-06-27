import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GLM_API_KEY = os.getenv("GLM_API_KEY")

# Set placeholders so provider clients don't fail at import time
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = "placeholder-deepseek-key"
    os.environ.setdefault("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY)
if not GLM_API_KEY:
    GLM_API_KEY = "placeholder-glm-key"

DEEPSEEK_MODEL = "deepseek:deepseek-chat"
GLM_MODEL_NAME = "glm-4-plus"
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")

DEEPSEEK_MODEL = "deepseek:deepseek-chat"
GLM_MODEL_NAME = "glm-4-plus"
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

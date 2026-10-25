from langchain_openai import ChatOpenAI
from app.config import AZURE_FOUNDRY_DEPLOYMENT, AZURE_FOUNDRY_ENDPOINT, AZURE_OPENAI_API_KEY

if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY is missing. Please add it to your .env file.")
if not AZURE_FOUNDRY_ENDPOINT:
    raise ValueError("AZURE_FOUNDRY_ENDPOINT is missing. Please add it to your .env file.")
if not AZURE_FOUNDRY_DEPLOYMENT:
    raise ValueError("AZURE_FOUNDRY_DEPLOYMENT is missing. Please add it to your .env file.")

# ─────────────────────────────────────────────
# LLM CLIENT
# ─────────────────────────────────────────────

_azure_llm = ChatOpenAI(
    model=AZURE_FOUNDRY_DEPLOYMENT,
    base_url=AZURE_FOUNDRY_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# All four names point to the same Azure client (kept for chain compatibility)
GPT_OSS_120B  = _azure_llm
GPT_OSS_20B   = _azure_llm
LLAMA_3_70B   = _azure_llm
LLAMA_4_SCOUT = _azure_llm

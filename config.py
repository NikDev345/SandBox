import os
from dotenv import load_dotenv
from SandBox.app.router_llm.gateway import LLMProviderSettings, GatewayConfig
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
APP_BASE_URL = os.getenv("APP_BASE_URL")
email_api_key = os.getenv('EMAIL_PASSWORD')
email_from = os.getenv('EMAIL_FROM')

def load_llm_config():
    provider = os.getenv("LLM_PROVIDER")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    # basic validation
    if not provider:
        raise ValueError("LLM_PROVIDER missing in .env")
    if not api_key:
        raise ValueError("LLM_API_KEY missing in .env")
    if not model:
        raise ValueError("LLM_MODEL missing in .env")

    provider_settings = LLMProviderSettings(
        provider=provider.lower(),
        api_key=api_key,
        model=model,
    )
    
    gateway_config = GatewayConfig()

    return provider_settings, gateway_config
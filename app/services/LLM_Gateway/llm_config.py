from app.services.LLM_Gateway.llm_gateway import LLMGateway
from app.models.gateway import GatewayConfig, ProviderConfig
from config import *

# gemini provider
gemini_provider = ProviderConfig(
    name="gemini",
    enabled=True,
    priority=1,

    default_model=GEMINI_MODEL,

    supported_models=[
        GEMINI_MODEL
    ],

    api_keys=GEMINI_KEYS,

    max_requests_per_minute=60,
    max_tokens_per_minute=None,
)

# openai provider
openai_provider = ProviderConfig(
    name="openai",
    enabled=True,
    priority=2,  # fallback after gemini

    default_model="gpt-4o-mini",

    supported_models=[
        "gpt-4o-mini",
        "gpt-4o",
    ],

    api_keys=OPENAI_KEYS,

    max_requests_per_minute=60,
    max_tokens_per_minute=None,
)

# gateway config
gateway_config = GatewayConfig(
    timeout=60,
    max_retries=3,
    retry_backoff=2.0,

    cache_enabled=True,
    cache_ttl=600,

    requests_per_minute=60,

    max_failures=5,
    cooldown_seconds=60,
)

providers = [gemini_provider]
if OPENAI_KEYS:
    providers.append(openai_provider)
gateway = LLMGateway(
    config=gateway_config,
    providers=providers,
)
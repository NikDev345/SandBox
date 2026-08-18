"""
LLM Configuration

Creates and exposes a single global gateway instance
used across all tools.
"""

from __future__ import annotations

import os
from typing import Optional, Type

from pydantic import BaseModel

# Import your core gateway implementation
from app.services.LLM_Gateway.llm_gateway import LLMGateway


# =====================================================
# ENV CONFIG
# =====================================================

class LLMSettings:
    """
    Central configuration for LLM behavior.
    """

    MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
    MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))

    # Optional logging/debug
    DEBUG: bool = os.getenv("LLM_DEBUG", "false").lower() == "true"


# =====================================================
# GATEWAY INSTANCE
# =====================================================

from app.router_llm.gateway import GatewayConfig, LLMProviderSettings

# Provider settings (API + model)
provider_settings = LLMProviderSettings(
    provider=os.getenv("LLM_PROVIDER", "gemini"),
    api_key=os.getenv("LLM_API_KEY"),
    model=os.getenv("LLM_MODEL", "gemini-1.5-flash"),
    base_url=os.getenv("LLM_BASE_URL"),  # optional
)

# Gateway config (retry + cache)
config = GatewayConfig(
    timeout=LLMSettings.TIMEOUT,
    max_retries=LLMSettings.MAX_RETRIES,
    retry_backoff=2,
    cache_enabled=True,
    cache_ttl=300,
)

# FINAL INSTANCE
gateway = LLMGateway(
    provider_settings=provider_settings,
    config=config,
)


# =====================================================
# OPTIONAL HELPER (STANDARDIZED CALL)
# =====================================================

async def generate(
    prompt: str,
    tool_slug: str,
    *,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    response_schema: Optional[Type[BaseModel]] = None,
    cache: bool = False,
):
    """
    Unified helper so services don’t repeat boilerplate.
    """

    from app.router_llm.gateway import LLMRequest

    response = await gateway.generate(
        LLMRequest(
            prompt=prompt,
            tool_slug=tool_slug,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_schema=response_schema,
            cache=cache,
        )
    )

    if not response or not response.text:
        raise RuntimeError("Empty response from LLM")

    return response
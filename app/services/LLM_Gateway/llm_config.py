"""
LLM Configuration

Creates and exposes a single global gateway instance
used across all tools.
"""

from __future__ import annotations

from typing import Optional, Type
from pydantic import BaseModel

# Core gateway
from app.services.LLM_Gateway.llm_gateway import LLMGateway

# Central config loader (ONLY source of truth)
from config import load_llm_config


# =====================================================
# LOAD CONFIG (Single Source of Truth)
# =====================================================

provider_settings, config = load_llm_config()


# =====================================================
# GLOBAL GATEWAY INSTANCE
# =====================================================

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
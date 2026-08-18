from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

class GatewayConfig(BaseModel):
    """Global configuration for the LLM Gateway."""

    timeout: int = 60

    max_retries: int = 3
    retry_backoff: float = 2.0

    cache_enabled: bool = True
    cache_ttl: int = 600


class LLMProviderSettings(BaseModel):
    """Single provider configuration loaded from ENV."""

    provider: str                 # "gemini" | "openai"
    api_key: str
    model: str

    base_url: str | None = None   # optional (for OpenAI-compatible APIs)

    max_requests_per_minute: int = 60
    max_tokens_per_minute: int | None = None

class LLMRequest(BaseModel):
    """Universal request object for every LLM call."""

    prompt: str
    system_prompt: str | None = None

    # Model override allowed (optional)
    model: str | None = None

    temperature: float = 0.3
    max_output_tokens: int = 8192

    contents: list[Any] = Field(default_factory=list)

    response_mime_type: str | None = None
    response_schema: type[BaseModel] | None = None

    cache: bool = True
    tool_slug: str = "unknown"

    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Standardized response returned by the gateway."""

    text: Any

    provider: str
    model: str

    cached: bool = False

    retries: int = 0

    latency_ms: float

    tokens_used: int | None = None

    finish_reason: str | None = None
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class NoAvailableKeyError(Exception):
    pass

class GatewayConfig(BaseModel):
    """Global configuration for the LLM Gateway."""

    timeout: int = 60
    max_retries: int = 3
    retry_backoff: float = 2.0

    cache_enabled: bool = True
    cache_ttl: int = 600

    requests_per_minute: int = 60

    max_failures: int = 5
    cooldown_seconds: int = 120


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str                          # gemini, openai, claude
    enabled: bool = True
    priority: int = 1                  # lower = higher priority

    default_model: str
    supported_models: list[str] = Field(default_factory=list)

    api_keys: list[str] = Field(default_factory=list)

    max_requests_per_minute: int = 60
    max_tokens_per_minute: int | None = None


class APIKeyState(BaseModel):
    """Runtime state of a single API key."""

    api_key: str

    healthy: bool = True
    failures: int = 0

    disabled_until: datetime | None = None

    requests_this_minute: int = 0
    tokens_this_minute: int = 0

    total_requests: int = 0
    total_failures: int = 0
    total_tokens: int = 0

    last_used: datetime | None = None
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class LLMRequest(BaseModel):
    """Universal request object for every LLM call."""

    # Prompt
    prompt: str
    system_prompt: str | None = None

    # Provider / Model
    provider: str | None = None          # None -> Auto select
    model: str | None = None             # None -> Provider default

    # Generation
    temperature: float = 0.3
    max_output_tokens: int = 8192

    # Inputs
    contents: list[Any] = Field(default_factory=list)

    # Output
    response_mime_type: str | None = None
    response_schema: type[BaseModel] | None = None

    # Gateway
    cache: bool = True
    tool_slug: str = "unknown"

    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Standardized response returned by the gateway."""

    text: str

    provider: str
    model: str

    cached: bool = False

    retries: int = 0

    latency_ms: float

    tokens_used: int | None = None

    finish_reason: str | None = None
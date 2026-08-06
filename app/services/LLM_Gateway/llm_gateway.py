from app.models.gateway import *
from config import *
import time, asyncio
from typing import Any
from google import genai
from google.genai import types

class LLMGateway:
    
    def __init__(self, config: GatewayConfig, providers: list[ProviderConfig]):
        self.config=config
        self.providers={provider.name: provider for provider in providers}
        self.key_states = {}
        self.clients = {}
        self.cache={}
        self.metrics = {
            "requests": 0,
            "success": 0,
            "failure": 0,
        }   
        self._rotation_index = {}

        for provider in providers:

            self.key_states[provider.name] = []
            self.clients[provider.name] = {}

            self._rotation_index[provider.name] = 0

            for api_key in provider.api_keys:

                self.key_states[provider.name].append(
                    APIKeyState(
                        api_key=api_key
                    )
                )

                self.clients[provider.name][api_key] = genai.Client(
                    api_key=api_key
                )
        
        
    async def generate(self, request: LLMRequest,) -> LLMResponse:
        provider = self._select_provider(request)
        self.metrics["requests"] += 1
        try:
            response = await self._call_provider(
                provider=provider,
                request=request,
            )
            self.metrics["success"] += 1
            return response
        except Exception:
            self.metrics["failure"] += 1
            raise
    
    def _select_provider(self, request: LLMRequest)->ProviderConfig:
        if request.provider:
            provider = self.providers.get(request.provider)
            
            if provider is None:
                raise ValueError(
                    f"Unknown provider '{request.provider}'."
                )
                
            if not provider.enabled:
                raise ValueError(
                    f"Provider '{request.provider}' is disabled."
                )
                
            return provider
        providers = sorted(
            [
                p for p in self.providers.values() if p.enabled
            ], key=lambda p:p.priority
        )
        if not providers:
            raise RuntimeError(
                "No providers available."
            )
        return providers[0]
            
    async def _call_provider(self, provider: ProviderConfig, request: LLMRequest) -> LLMResponse:
        client, key_state = self._get_client(provider)
        if provider.name.lower() == 'gemini':
            return await self._call_gemini(
                client=client,
                key_state=key_state,
                provider=provider,
                request=request,
            )
        raise NotImplementedError(
            provider.name
        )
        
    def _build_contents(self, request: LLMRequest) -> list[Any]:
        contents = []
        if request.contents:
            contents.extend(request.contents)
            
        contents.append(types.Part.from_text(text=request.prompt))
        return contents
    
    async def _call_gemini(self, client, key_state: APIKeyState, provider: ProviderConfig, request: LLMRequest) -> LLMResponse:
        try:
            start = time.perf_counter()
            
            model = (request.model or provider.default_model)
            config = types.GenerateContentConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_output_tokens,
            )
            if request.response_mime_type:
                config.response_mime_type = (request.response_mime_type)
            
            response = await client.aio.models.generate_content(
                model=model,
                contents=self._build_contents(request=request),
                config=config
            )
            latency=(
                time.perf_counter() - start
            ) * 1000
            key_state.total_requests += 1
            key_state.last_used = datetime.utcnow()
            usage = getattr(response, "usage_metadata", None)
            if usage:
                key_state.total_tokens += (
                    usage.total_token_count or 0
                )
            
            return LLMResponse(
                text=response.text or "",
                provider=provider.name,
                model=model,
                cached=False,
                retries=0,
                latency_ms=latency,
                tokens_used=(
                    getattr(
                        usage,
                        "total_token_count",
                        None,
                    )
                    if usage
                    else None
                ),
                finish_reason=(
                    response.candidates[0].finish_reason.name
                    if response.candidates
                    else None
                ),
            )
        except Exception:
            key_state.failures += 1
            key_state.total_failures += 1
            raise
        
    def _get_api_key_state(self, provider: ProviderConfig) -> APIKeyState:
        states = self.key_states[provider.name]
        index = self._rotation_index[provider.name]
        
        state = states[index]
        
        self._rotation_index[provider.name] = (index + 1) % len(states)
        return state
    
    def _get_client(self, provider: ProviderConfig):
        key_state = self._get_api_key_state(provider)
        
        client = self.clients[provider.name][key_state.api_key]
        return client, key_state
    
    def _is_retryable_exception(self, error: Exception) -> bool:
        
        message = str(error).lower()
        retryable = (
            "429" in message
            or "500" in message
            or "502" in message
            or "503" in message
            or "504" in message
            or "timeout" in message
            or "connection" in message
            or "temporarily unavailable" in message
            or "resource exhausted" in message
            or "rate limit" in message
        )   
        return retryable
    
    async def _execute_request(self, provider: ProviderConfig, request: LLMRequest)->LLMResponse:
        ...
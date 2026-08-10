from app.models.gateway import *
from config import *
import time, asyncio, json, hashlib
from typing import Any
from google import genai
from google.genai import types
from datetime import timedelta, datetime
from openai import OpenAI

class LLMGateway:
    
    def __init__(self, config: GatewayConfig, providers: list[ProviderConfig]):
        self.config=config
        self.providers={provider.name: provider for provider in providers}
        self.key_states = {}
        self.clients = {}
        self.cache={}
        self.metrics = {
            "request_total": 0,
            "success_total": 0,
            "failure_total": 0,
            "retries_total": 0,
            "provider_fallbacks": 0,
            "cache_hits": 0,
            "cache_miss": 0,
            "total_latency_ms": 0,
            "tool_usage": {}
        }   
        self._rotation_index = {}

        for provider in providers:

            self.key_states[provider.name] = []
            self.clients[provider.name] = {}

            self._rotation_index[provider.name] = 0

            for api_key in provider.api_keys:

                self.key_states[provider.name].append(
                    APIKeyState(api_key=api_key)
                )

                if provider.name == "gemini":
                    self.clients[provider.name][api_key] = genai.Client(
                        api_key=api_key
                    )

                elif provider.name == "openai":
                    self.clients[provider.name][api_key] = OpenAI(
                        api_key=api_key
                    )
        
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.metrics["request_total"] += 1

        # tool usage
        tool = request.tool_slug or "unknown"
        self.metrics["tool_usage"][tool] = self.metrics["tool_usage"].get(tool, 0) + 1

        # -------------------------
        # Cache check (same as yours)
        # -------------------------
        should_cache = self.config.cache_enabled and self._should_cache(request)
        if should_cache:
            key = self._build_cache_key(request)
            entry = self.cache.get(key)
            if entry:
                response, expiry = entry
                if datetime.utcnow() < expiry:
                    self.metrics["cache_hits"] += 1
                    response.cached = True
                    return response
                else:
                    del self.cache[key]
            self.metrics["cache_miss"] += 1

        # -------------------------
        #  Build provider chain
        # -------------------------
        if request.provider:
            provider_chain = [self._select_provider(request)]
        else:
            provider_chain = sorted(
                [p for p in self.providers.values() if p.enabled],
                key=lambda p: p.priority
            )

        last_error = None

        # -------------------------
        # Try providers one by one
        # -------------------------
        for idx, provider in enumerate(provider_chain):
            try:
                response = await self._execute_request(
                    provider=provider,
                    request=request,
                )

                self.metrics["success_total"] += 1
                self.metrics["total_latency_ms"] += response.latency_ms

                # cache store
                if should_cache:
                    expiry = datetime.utcnow() + timedelta(seconds=self.config.cache_ttl)
                    self.cache[key] = (response, expiry)

                return response
            
            except NoAvailableKeyError as e:
                #  KEY POINT: switch provider immediately
                last_error = e

                if idx < len(provider_chain) - 1:
                    self.metrics["provider_fallbacks"] += 1
                    continue
                else:
                    raise

            except Exception as e:
                last_error = e

                # If user forced provider → don't fallback
                if request.provider:
                    self.metrics["failure_total"] += 1
                    raise

                # If not retryable → stop immediately
                if not self._is_retryable_exception(e):
                    self.metrics["failure_total"] += 1
                    raise

                # Try next provider
                if idx < len(provider_chain) - 1:
                    self.metrics["provider_fallbacks"] = (
                        self.metrics.get("provider_fallbacks", 0) + 1
                    )
                    continue

        # All providers failed
        self.metrics["failure_total"] += 1
        raise last_error
    
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
            
        elif provider.name.lower() == "openai":
            return await self._call_openai(
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
        if request.system_prompt:
            contents.append(
                types.Part.from_text(text=request.system_prompt)
            )
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
                tokens = usage.total_token_count or 0
                key_state.total_tokens += tokens
                key_state.tokens_this_minute += tokens
            else:
                tokens = 0
                
            key_state.requests_this_minute += 1 
            key_state.failures = 0
            key_state.healthy = True
            key_state.disabled_until = None
            
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
        except Exception as e:
            if self._is_retryable_exception(e):
                key_state.failures += 1
                key_state.total_failures += 1
                if key_state.failures >= self.config.max_failures:
                    key_state.healthy = False
                    key_state.disabled_until = datetime.utcnow() + timedelta(seconds=self.config.cooldown_seconds)
            raise
    
    async def _call_openai(
        self,
        client,
        key_state: APIKeyState,
        provider: ProviderConfig,
        request: LLMRequest,
    ) -> LLMResponse:
        try:
            start = time.perf_counter()
            model = request.model or provider.default_model
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })

            messages.append({
                "role": "user",
                "content": request.prompt
            })

            # OpenAI is sync → wrap in thread
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
            )
            latency = (time.perf_counter() - start) * 1000

            # usage
            usage = getattr(response, "usage", None)
            tokens = usage.total_tokens if usage else 0

            # update key state
            key_state.total_requests += 1
            key_state.total_tokens += tokens
            key_state.tokens_this_minute += tokens
            key_state.requests_this_minute += 1
            key_state.last_used = datetime.utcnow()

            key_state.failures = 0
            key_state.healthy = True
            key_state.disabled_until = None

            return LLMResponse(
                text=response.choices[0].message.content,
                provider=provider.name,
                model=model,
                cached=False,
                retries=0,
                latency_ms=latency,
                tokens_used=tokens,
                finish_reason=response.choices[0].finish_reason,
            )

        except Exception as e:
            if self._is_retryable_exception(e):
                key_state.failures += 1
                key_state.total_failures += 1

                if key_state.failures >= self.config.max_failures:
                    key_state.healthy = False
                    key_state.disabled_until = datetime.utcnow() + timedelta(
                        seconds=self.config.cooldown_seconds
                    )

            raise    
    
    def _get_api_key_state(self, provider: ProviderConfig) -> APIKeyState:
        states = self.key_states[provider.name]
        index = self._rotation_index[provider.name]
        
        state = states[index]
        
        self._rotation_index[provider.name] = (index + 1) % len(states)
        return state
    
    def _get_client(self, provider: ProviderConfig):
        states = self.key_states[provider.name] #key_states["gemini"] = 2 api keys until now.
        total = len(states)
        now = datetime.utcnow()
        
        for _ in range(total):
            key_state = self._get_api_key_state(provider)
            # recover if cooldown finish
            if key_state.disabled_until:
                if key_state.disabled_until <= now:
                    key_state.healthy = True
                    key_state.failures = 0
                    key_state.disabled_until = None
            if not key_state.healthy:
                continue
            # reset rate limit window
            if (now - key_state.last_reset).total_seconds() >= 60:
                key_state.requests_this_minute = 0
                key_state.tokens_this_minute = 0
                key_state.last_reset = now
            # rate limit check
            if key_state.requests_this_minute >= provider.max_requests_per_minute:
                continue
            if provider.max_tokens_per_minute is not None and key_state.tokens_this_minute >= provider.max_tokens_per_minute:
                continue
            client = self.clients[provider.name][key_state.api_key]
            print("Using key:", key_state.api_key)
            return client, key_state
        raise NoAvailableKeyError(f"No healthy keys for provider {provider.name}")
    
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
        
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await self._call_provider(provider=provider, request=request)
            except NoAvailableKeyError:
                # No keys → don't retry → propagate to fallback
                raise
            except Exception as e:
                last_error = e
                
                if not self._is_retryable_exception(e):
                    raise
                
                if attempt == self.config.max_retries:
                    break
                
                self.metrics["retries_total"] += 1
                delay = self.config.retry_backoff ** attempt
                await asyncio.sleep(delay)
        raise last_error
    
    def _build_cache_key(self, request: LLMRequest) -> str:
        key_data = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "model": request.model,
            "provider": request.provider,
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
            "tool": request.tool_slug,
            "contents": str(request.contents),  # simple fallback
        }
        
        raw = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_metrics(self) -> dict:
        total_requests = self.metrics["request_total"]
        total_latency = self.metrics["total_latency_ms"]

        avg_latency = (
            total_latency / self.metrics["success_total"]
            if self.metrics["success_total"] > 0
            else 0
        )

        total_cache = self.metrics["cache_hits"] + self.metrics["cache_miss"]

        cache_hit_rate = (
            self.metrics["cache_hits"] / total_cache
            if total_cache > 0
            else 0
        )

        return {
            "requests": total_requests,
            "success": self.metrics["success_total"],
            "failure": self.metrics["failure_total"],
            "retries": self.metrics["retries_total"],

            "cache_hits": self.metrics["cache_hits"],
            "cache_miss": self.metrics["cache_miss"],
            "cache_hit_rate": round(cache_hit_rate, 3),

            "avg_latency_ms": round(avg_latency, 2),

            "tool_usage": self.metrics["tool_usage"],
        }
        
    def _should_cache(self, request: LLMRequest) -> bool:
        if not request.cache: return False
        # skip if content exists(files/images)
        if request.contents: return False
        # skip very large prompts
        if len(request.prompt) > 5000: return False
        # skip tools 
        NON_CACHEABLE_TOOLS = {
            "image_text_extractor",
            "chart_explainer",
            "table_extractor",
            "sql_generator",
            "commit_msg",
            "item_extractor",
            "code_reviewer",
            "docker_generator",
            "notes_cleaner",
            "ss_explainer",
            "mock_api"
        }
        if request.tool_slug in NON_CACHEABLE_TOOLS: return False
        # Skip real-time queries (basic heuristic)
        realtime_keywords = [
            "today", "now", "current", "latest", "live", "price", "stock"
        ]
        prompt_lower = request.prompt.lower()
        if any(word in prompt_lower for word in realtime_keywords):
            return False
        
        return True
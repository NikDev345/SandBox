import time
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from SandBox.app.router_llm.gateway import LLMRequest, LLMResponse, GatewayConfig
from app.services.LLM_Gateway.llm_client import LLMClientFactory

class LLMGateway:

    def __init__(self, provider_settings, config: GatewayConfig):
        self.client = LLMClientFactory.create(provider_settings)
        self.config = config
        self.cache = {}
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_total = time.perf_counter()

        # ---------- Cache ----------
        key = None
        if self.config.cache_enabled and request.cache:
            key = self._build_cache_key(request)

            if key in self.cache:
                response, expiry = self.cache[key]
                if datetime.utcnow() < expiry:
                    response.cached = True
                    return response
                else:
                    del self.cache[key]

        # ---------- Retry ----------
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.generate(request)

                # store cache
                if key:
                    expiry = datetime.utcnow() + timedelta(seconds=self.config.cache_ttl)
                    self.cache[key] = (response, expiry)

                return response

            except Exception as e:
                last_error = e

                if attempt == self.config.max_retries:
                    break

                delay = self.config.retry_backoff ** attempt
                await asyncio.sleep(delay)

        raise last_error
    
    def _build_cache_key(self, request: LLMRequest) -> str:
        key_data = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
        }

        raw = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    
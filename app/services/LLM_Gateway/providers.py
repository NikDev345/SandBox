import time, asyncio
from google import genai
from google.genai import types
from app.models.gateway import LLMRequest, LLMResponse
from openai import OpenAI

# gemini client
class GeminiClient:
    def __init__(self, settings):
        self.settings = settings
        self.client = genai.Client(api_key=settings.api_key)
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        start = time.perf_counter()
        model = request.model or self.settings.model
        
        contents = []
        if request.system_prompt:
            contents.append(types.Part.from_text(text=request.system_prompt))
        contents.append(types.Part.from_text(text=request.prompt))
        
        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens
        )
        
        if request.response_mime_type:
            config.response_mime_type = request.response_mime_type
            
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        latency = (time.perf_counter() - start) * 1000
        
        return LLMResponse(
            text=response.text or "",
            provider="gemini",
            model=model,
            latency_ms=latency,
            tokens_used=getattr(
                getattr(response, "usage_metadata", None),
                "total_token_count",
                None
            ),
            finish_reason=(
                response.candidates[0].finish_reason.name
                if response.candidates else None
            ),
        )
        
class OpenAIClient:
    def __init__(self, settings):
        self.settings = settings
        
        if settings.base_url:
            self.client = OpenAI(
                api_key=settings.api_key,
                base_url=settings.base_url
            )
        else:
            self.client = OpenAI(api_key=settings.api_key)
            
    async def generate(self, request: LLMRequest) -> LLMResponse:
        start = time.perf_counter()
        
        model = request.model or self.settings.model
        
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
        
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_output_tokens
        )
        
        latency = (time.perf_counter() - start) * 1000

        usage = getattr(response, "usage", None)
        tokens = usage.total_tokens if usage else None

        return LLMResponse(
            text=response.choices[0].message.content,
            provider="openai",
            model=model,
            latency_ms=latency,
            tokens_used=tokens,
            finish_reason=response.choices[0].finish_reason,
        )
        

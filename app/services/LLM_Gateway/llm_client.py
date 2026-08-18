from app.router_llm.gateway import LLMProviderSettings
from app.services.LLM_Gateway.providers import GeminiClient, OpenAIClient

# later you will add more:
# from app.providers.claude import ClaudeClient
# from app.providers.groq import GroqClient
# from app.providers.deepseek import DeepSeekClient


class LLMClientFactory:

    PROVIDER_MAP = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        # "claude": ClaudeClient,
        # "groq": GroqClient,
        # "deepseek": DeepSeekClient,
    }

    @classmethod
    def create(cls, settings: LLMProviderSettings):
        provider = settings.provider.lower()

        if provider not in cls.PROVIDER_MAP:
            raise ValueError(f"Unsupported provider: {provider}")

        client_class = cls.PROVIDER_MAP[provider]
        return client_class(settings)
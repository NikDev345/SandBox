import asyncio

from config import load_llm_config
from app.services.LLM_Gateway.llm_gateway import LLMGateway
from SandBox.app.router_llm.gateway import LLMRequest

provider_settings, gateway_config = load_llm_config()

gateway = LLMGateway(provider_settings, gateway_config)

async def main():
    response = await gateway.generate(
        LLMRequest(
            prompt="Explain AI in 2 lines"
        )
    )

    print("Provider:", response.provider)
    print("Model:", response.model)
    print("Response:", response.text)


asyncio.run(main())
from app.services.gemini_service import GeminiService

gemini = GeminiService()

response = gemini.generate(
    "Say hello in one sentence."
)

print(response)
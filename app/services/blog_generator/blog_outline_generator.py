from app.models.blog_outline_generator import (
    BlogOutlineRequest,
    BlogOutlineResponse,
)
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine


class BlogOutlineGeneratorService:

    @staticmethod
    async def generate(
        request: BlogOutlineRequest,
    ) -> BlogOutlineResponse:

        prompt = PromptEngine.build_blog_outline_prompt(request)

        gemini = GeminiService()

        result = gemini.generate(prompt)

        return BlogOutlineResponse(
            outline=result,
            usage=None,
        )
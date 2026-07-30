from app.models.blog_outline_generator import (
    BlogOutlineRequest,
    BlogOutlineResponse,
)
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class BlogOutlineGeneratorService:

    @staticmethod
    async def generate(
        request: BlogOutlineRequest,
        user_id: str,
        db: Session
    ) -> BlogOutlineResponse:

        prompt = PromptEngine.build_blog_outline_prompt(request)

        gemini = GeminiService()

        result = gemini.generate(prompt)
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="BLOG_GENERATOR",
            )
        tool_id = tool.id if tool else "BLOG_GENERATOR"
        
        try:
            ExecutionService.create_execution(
            db=db,
            user_id=user_id,
            tool_id=tool_id,
            user_input=request.topic,
            output=result,
            )
        except Exception:
            pass

        return BlogOutlineResponse(
            outline=result,
            usage=None,
        )
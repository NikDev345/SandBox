from app.models.blog_outline_generator import (
    BlogOutlineRequest,
    BlogOutlineResponse,
)
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session
import json

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
        
        user_input = json.dumps({
            "topic": request.topic,
            "audience": request.audience,
            "goal": request.goal,
            "tone": request.tone,
            "depth": request.depth,
            "sections": request.sections,
            "language": request.language,
            "include_introduction": request.include_introduction,
            "include_conclusion": request.include_conclusion,
            "include_faqs": request.include_faqs,
            "include_cta": request.include_cta,
            "include_statistics": request.include_statistics,
            "include_examples": request.include_examples,
            "include_case_studies": request.include_case_studies,
            "include_internal_links": request.include_internal_links,
            "include_external_resources": request.include_external_resources,
            "include_key_takeaways": request.include_key_takeaways,
            "primary_keyword": request.primary_keyword,
            "secondary_keywords": request.secondary_keywords,
        })
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="BLOG-OUTLINE-GENERATOR",
            )
        tool_id = tool.id if tool else "BLOG-OUTLINE-GENERATOR"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
            db=db,
            user_id=user_id,
            tool_id=tool_id,
            user_input=user_input,
            output=result,
            )
            execution_id = execution.id if execution else None
        except Exception:
            pass

        return BlogOutlineResponse(
            outline=result,
            usage=None,
            execution_id=execution_id,
        )
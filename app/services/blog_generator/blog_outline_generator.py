from app.models.blog_outline_generator import (
    BlogOutlineRequest,
    BlogOutlineResponse,
)
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
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
        
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)

        prompt = PromptEngine.build_blog_outline_prompt(request)

        llm_response = await gateway.generate(LLMRequest(
            prompt=prompt,
            tool_slug="blog_generator",
            temperature=0.7,
        ))
        if not llm_response or not llm_response.text:
            raise ValueError("Empty response from LLM")

        result = llm_response.text.strip()
        
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
                slug="blog_generator",
            )
        tool_id = tool.id if tool else "blog_generator"
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
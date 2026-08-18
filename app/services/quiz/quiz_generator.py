"""
Quiz Generator Service
----------------------
Coordinates the complete Quiz Generator workflow.
"""

from app.models.quiz_generator import (
    QuizRequest,
    QuizResponse,
    QuizLLMResponse
)

from app.services.quiz.parser import DocumentParser
from app.services.quiz.prompt_engine import PromptEngine
from app.services.quiz.validator import QuizValidator
from app.services.quiz.formatter import QuizFormatter
from app.utils.text_cleaner import TextCleaner
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session
import json
class QuizGeneratorService:
    """
    Orchestrates the Quiz Generator workflow.
    """

    async def generate_quiz(
        self,
        request: QuizRequest,
        db: Session,
        user=None,
    ) -> QuizResponse:
        """
        Generate a quiz.
        """
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user['sub'])
        # --------------------------------------------------
        # Validate Request
        # --------------------------------------------------

        QuizValidator.validate_request(request)


        # --------------------------------------------------
        # Clean Text
        # --------------------------------------------------
        if request.input_type.value == "document":

            request.extracted_text = TextCleaner.clean(
                request.extracted_text
            )

        else:

            request.prompt = TextCleaner.clean(
                request.prompt
            )

        # --------------------------------------------------
        # Build Prompt
        # --------------------------------------------------

        prompt = PromptEngine.build_prompt(
            request
        )

        # --------------------------------------------------
        # Generate Quiz
        # --------------------------------------------------


        result = await gateway.generate(
            LLMRequest(
                prompt=prompt,
                tool_slug="quiz_generator",
                temperature=0.5,
                max_output_tokens=8000,
                response_schema=QuizLLMResponse, 
            )
        )

        response_json = result.text

        # --------------------------------------------------
        # Format Response
        # --------------------------------------------------
        if not result or not result.text:
            raise RuntimeError("Empty response from LLM")

        if not isinstance(result.text, dict):
            raise RuntimeError("Invalid structured response")

        llm_data = QuizLLMResponse(**result.text)
        if not llm_data.questions:
            raise RuntimeError("LLM returned empty quiz")
        response = QuizFormatter.format(llm_data.model_dump())

        # --------------------------------------------------
        # Validate AI Response
        # --------------------------------------------------

        QuizValidator.validate_response(
            response,
            request,
        )
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="quiz_generator",
            )
        tool_id = tool.id if tool else "quiz_generator"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user['sub'],
                tool_id=tool_id,
                user_input=request.model_dump_json(),
                output=json.dumps(response.model_dump()),
            )
            execution_id = execution.id
        except Exception:
            pass
        response.execution_id = execution_id
        return response
"""
Quiz Generator Service
----------------------
Coordinates the complete Quiz Generator workflow.
"""

from app.models.quiz_generator import (
    QuizRequest,
    QuizResponse,
)

from app.services.quiz.parser import DocumentParser
from app.services.quiz.prompt_engine import PromptEngine
from app.services.quiz.validator import QuizValidator
from app.services.quiz.formatter import QuizFormatter
from app.utils.text_cleaner import TextCleaner
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

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

        # --------------------------------------------------
        # Validate Request
        # --------------------------------------------------

        QuizValidator.validate_request(request)


        # --------------------------------------------------
        # Clean Text
        # --------------------------------------------------
        ip = ""
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


        result = await gateway.generate(LLMRequest(
            prompt=prompt,
            tool_slug="quiz_generator",
            response_mime_type="application/json",
            temperature=0.6,
        ))

        response_json = result.text

        # --------------------------------------------------
        # Format Response
        # --------------------------------------------------

        response = QuizFormatter.format(
            response_json
        )

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
                output=str(response.questions),
            )
            execution_id = execution.id
        except Exception:
            pass
        response.execution_id = execution_id
        return response
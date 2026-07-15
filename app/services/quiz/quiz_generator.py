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
from app.services.gemini_service import GeminiService
from app.utils.text_cleaner import TextCleaner


class QuizGeneratorService:
    """
    Orchestrates the Quiz Generator workflow.
    """

    async def generate_quiz(
        self,
        request: QuizRequest,
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

        gemini = GeminiService()

        response_json = await gemini.generate_json(
            prompt=prompt
        )

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

        return response
"""
Quiz Prompt Engine
------------------
Builds prompts for the Quiz Generator.
"""

from app.models.quiz_generator import QuizRequest
from app.services.quiz.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class PromptEngine:
    """
    Responsible for constructing prompts for the AI model.
    """

    @staticmethod
    def build_prompt(request: QuizRequest) -> str:
        """
        Build the final prompt sent to Gemini.

        Args:
            request: Quiz generation request.

        Returns:
            Fully formatted prompt.
        """

        content = (
            request.prompt.strip()
            if request.input_type.value == "prompt"
            else request.extracted_text.strip()
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            question_count=request.settings.question_count,
            difficulty=request.settings.difficulty.value,
            audience=request.settings.audience.value,
            language=request.settings.language.value,
            question_types=", ".join(
                qt.value for qt in request.settings.question_types
            ),
            include_explanations=request.settings.include_explanations,
            include_hints=request.settings.include_hints,
            content=content,
        )

        return f"{SYSTEM_PROMPT}\n\n{user_prompt}"
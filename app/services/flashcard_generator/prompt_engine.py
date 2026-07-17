"""
Flashcard Generator Prompt Engine
---------------------------------
Builds prompts for the Flashcard Generator.
"""

from app.models.flashcard_generator import FlashcardGeneratorRequest
from app.services.flashcard_generator.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class PromptEngine:
    """
    Responsible for constructing prompts for the AI model.
    """

    @staticmethod
    def build_prompt(request: FlashcardGeneratorRequest) -> str:
        """
        Build the final prompt sent to Gemini.
        """

        settings = request.settings

        user_prompt = USER_PROMPT_TEMPLATE.format(
            number_of_cards=settings.number_of_cards,
            difficulty=settings.difficulty.value,
            card_type=settings.card_type.value,
            language=settings.language.value,
            include_examples=settings.include_examples,
            include_memory_tips=settings.include_memory_tips,
            include_keywords=settings.include_keywords,
            include_tags=settings.include_tags,
            content=request.content.strip(),
        )

        return f"{SYSTEM_PROMPT}\n\n{user_prompt}"

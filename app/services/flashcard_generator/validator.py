"""
Flashcard Generator Validator
-----------------------------
Validates flashcard requests and AI responses.
"""

from app.models.flashcard_generator import (
    FlashcardGeneratorRequest,
    FlashcardGeneratorResponse,
)


class FlashcardGeneratorValidator:
    """
    Performs validation before and after flashcard generation.
    """

    MIN_CONTENT_LENGTH = 3
    MAX_CONTENT_LENGTH = 50000
    MIN_CARD_COUNT = 1
    MAX_CARD_COUNT = 100

    @classmethod
    def validate_request(
        cls,
        request: FlashcardGeneratorRequest,
    ) -> None:
        """
        Validate incoming request before calling Gemini.
        """

        if not request.content:
            raise ValueError("Content cannot be empty.")

        if not request.content.strip():
            raise ValueError("Content cannot be blank.")

        content_length = len(request.content.strip())

        if content_length < cls.MIN_CONTENT_LENGTH:
            raise ValueError(
                "Content is too short to generate flashcards."
            )

        if content_length > cls.MAX_CONTENT_LENGTH:
            raise ValueError(
                "Input content exceeds maximum supported length."
            )

        settings = request.settings

        if (
            settings.number_of_cards < cls.MIN_CARD_COUNT
            or settings.number_of_cards > cls.MAX_CARD_COUNT
        ):
            raise ValueError(
                f"Number of cards must be between "
                f"{cls.MIN_CARD_COUNT} and "
                f"{cls.MAX_CARD_COUNT}."
            )

        if not settings.difficulty:
            raise ValueError("Difficulty is required.")

        if not settings.card_type:
            raise ValueError("Card type is required.")

        if not settings.language:
            raise ValueError("Language is required.")

    @classmethod
    def validate_response(
        cls,
        response: FlashcardGeneratorResponse,
        request: FlashcardGeneratorRequest,
    ) -> None:
        """
        Validate Gemini response after formatting.
        """

        if not response.success:
            raise ValueError("Flashcard generation failed.")

        flashcards = response.result.flashcards

        if len(flashcards) != request.settings.number_of_cards:
            raise ValueError(
                "Generated flashcard count does not match request."
            )

        if response.result.statistics.total_cards != len(flashcards):
            raise ValueError(
                "Flashcard statistics count mismatch."
            )

        fronts = set()

        for flashcard in flashcards:

            if not flashcard.front.strip():
                raise ValueError("Flashcard front cannot be empty.")

            if not flashcard.back.strip():
                raise ValueError("Flashcard back cannot be empty.")

            front_key = flashcard.front.strip().lower()

            if front_key in fronts:
                raise ValueError(
                    f"Duplicate flashcard front: {flashcard.front}"
                )

            fronts.add(front_key)

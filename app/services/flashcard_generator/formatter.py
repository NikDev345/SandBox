"""
Flashcard Generator Formatter
-----------------------------
Converts Gemini JSON into strongly typed FlashcardGeneratorResponse models.
"""

from app.models.flashcard_generator import (
    Flashcard,
    FlashcardDifficulty,
    FlashcardGeneratorResponse,
    FlashcardLanguage,
    FlashcardResult,
    FlashcardSettings,
    FlashcardStatistics,
    FlashcardType,
)


class FlashcardGeneratorFormatter:
    """
    Responsible for converting raw Gemini JSON into FlashcardGeneratorResponse.
    """

    @staticmethod
    def format(
        data: dict,
        settings: FlashcardSettings,
    ) -> FlashcardGeneratorResponse:
        """
        Convert Gemini JSON into FlashcardGeneratorResponse.
        """

        raw_flashcards = data.get("flashcards", [])

        flashcards = []

        for index, item in enumerate(raw_flashcards, start=1):

            tags = (
                item.get("tags", [])
                if settings.include_tags
                else []
            )

            keywords = (
                item.get("keywords", [])
                if settings.include_keywords
                else []
            )

            flashcard = Flashcard(
                id=item.get("id", str(index)),
                front=item["front"],
                back=item["back"],
                card_type=item.get(
                    "card_type",
                    settings.card_type,
                ),
                difficulty=item.get(
                    "difficulty",
                    settings.difficulty,
                ),
                category=item.get("category", "General"),
                tags=tags if isinstance(tags, list) else [],
                keywords=keywords if isinstance(keywords, list) else [],
                example=(
                    item.get("example")
                    if settings.include_examples
                    else None
                ),
                memory_tip=(
                    item.get("memory_tip")
                    if settings.include_memory_tips
                    else None
                ),
            )

            flashcards.append(flashcard)

        categories = sorted(
            {
                flashcard.category
                for flashcard in flashcards
                if flashcard.category
            }
        )

        statistics = FlashcardStatistics(
            total_cards=len(flashcards),
            estimated_study_time_minutes=max(1, len(flashcards) * 2),
            difficulty=FlashcardDifficulty(
                data.get("difficulty", settings.difficulty)
            ),
            card_type=FlashcardType(
                data.get("card_type", settings.card_type)
            ),
            language=FlashcardLanguage(
                data.get("language", settings.language)
            ),
            categories=categories,
            total_keywords=sum(
                len(flashcard.keywords)
                for flashcard in flashcards
            ),
            total_tags=sum(
                len(flashcard.tags)
                for flashcard in flashcards
            ),
        )

        result = FlashcardResult(
            title=data.get("title", "Generated Flashcards"),
            description=data.get("description"),
            flashcards=flashcards,
            statistics=statistics,
        )

        return FlashcardGeneratorResponse(
            success=True,
            result=result,
        )

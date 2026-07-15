"""
Quiz Formatter
--------------
Converts Gemini JSON into strongly typed QuizResponse models.
"""

from app.models.quiz_generator import (
    QuizMetadata,
    QuizOption,
    QuizQuestion,
    QuizResponse,
)


class QuizFormatter:
    """
    Responsible for converting raw Gemini JSON into QuizResponse.
    """

    @staticmethod
    def format(data: dict) -> QuizResponse:
        """
        Convert Gemini JSON into QuizResponse.
        """

        metadata = QuizMetadata(
            title=data.get("title", "Generated Quiz"),
            description=data.get("description"),
            total_questions=len(data.get("questions", [])),
            estimated_time_minutes=data.get(
                "estimated_time_minutes",
                10,
            ),
            language=data.get("language", "english"),
            difficulty=data.get("difficulty", "medium"),
        )

        questions = []

        for index, item in enumerate(data.get("questions", []), start=1):

            options = [
                QuizOption(
                    id=option["id"],
                    text=option["text"],
                )
                for option in item.get("options", [])
            ]

            question = QuizQuestion(
                id=item.get("id", str(index)),
                question=item["question"],
                question_type=item["question_type"],
                options=options,
                correct_answers=item.get(
                    "correct_answers",
                    [],
                ),
                explanation=item.get("explanation"),
                hint=item.get("hint"),
                difficulty=item.get(
                    "difficulty",
                    "medium",
                ),
                marks=item.get("marks", 1),
            )

            questions.append(question)

        return QuizResponse(
            success=True,
            metadata=metadata,
            questions=questions,
        )
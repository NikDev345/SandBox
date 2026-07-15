"""
Quiz Validator
--------------
Validates quiz requests and AI responses.
"""

from app.models.quiz_generator import (
    QuizRequest,
    QuizResponse,
)


class QuizValidator:
    """
    Performs validation before and after quiz generation.
    """

    MAX_CONTENT_LENGTH = 50000
    MIN_QUESTION_COUNT = 1
    MAX_QUESTION_COUNT = 100

    # ==========================================================
    # REQUEST VALIDATION
    # ==========================================================

    @classmethod
    def validate_request(cls, request: QuizRequest) -> None:
        """
        Validate incoming request before calling Gemini.
        """

        if request.input_type.value == "prompt":

            if not request.prompt:
                raise ValueError("Prompt cannot be empty.")

            if not request.prompt.strip():
                raise ValueError("Prompt cannot be blank.")

        else:

            if not request.extracted_text:
                raise ValueError("Document contains no text.")

            if not request.extracted_text.strip():
                raise ValueError("Document contains no readable text.")

        settings = request.settings

        if (
            settings.question_count < cls.MIN_QUESTION_COUNT
            or settings.question_count > cls.MAX_QUESTION_COUNT
        ):
            raise ValueError(
                f"Question count must be between "
                f"{cls.MIN_QUESTION_COUNT} and "
                f"{cls.MAX_QUESTION_COUNT}."
            )

        content = (
            request.prompt
            if request.input_type.value == "prompt"
            else request.extracted_text
        )

        if len(content) > cls.MAX_CONTENT_LENGTH:
            raise ValueError(
                "Input content exceeds maximum supported length."
            )

        if not settings.question_types:
            raise ValueError(
                "At least one question type is required."
            )

    # ==========================================================
    # RESPONSE VALIDATION
    # ==========================================================

    @classmethod
    def validate_response(
        cls,
        response: QuizResponse,
        request: QuizRequest,
    ) -> None:
        """
        Validate Gemini response.
        """

        if not response.success:
            raise ValueError("Quiz generation failed.")

        if response.metadata.total_questions != request.settings.question_count:
            raise ValueError(
                "Generated question count does not match request."
            )

        if len(response.questions) != request.settings.question_count:
            raise ValueError(
                "Question list length mismatch."
            )

        question_ids = set()

        for question in response.questions:

            if question.id in question_ids:
                raise ValueError(
                    f"Duplicate question id: {question.id}"
                )

            question_ids.add(question.id)

            if not question.question.strip():
                raise ValueError(
                    "Question text cannot be empty."
                )

            if question.question_type.value == "mcq":

                if len(question.options) != 4:
                    raise ValueError(
                        "MCQ must contain exactly four options."
                    )

                if len(question.correct_answers) != 1:
                    raise ValueError(
                        "MCQ must have exactly one correct answer."
                    )

            if question.marks <= 0:
                raise ValueError(
                    "Marks must be greater than zero."
                )
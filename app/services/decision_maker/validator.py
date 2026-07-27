"""
============================================================
Decision Maker Validator

Validates incoming requests before they are processed
by the Decision Maker service.

Author: Sandbox AI
============================================================
"""

from typing import Set

from app.models.decision_maker import DecisionMakerRequest


class DecisionMakerValidator:
    """Validation utilities for Decision Maker."""

    @staticmethod
    def validate(request: DecisionMakerRequest) -> None:
        """
        Validate the complete request.

        Raises:
            ValueError: If validation fails.
        """

        DecisionMakerValidator._validate_question(request.question)
        DecisionMakerValidator._validate_options(request)
        DecisionMakerValidator._validate_criteria(request)

    # ========================================================
    # QUESTION
    # ========================================================

    @staticmethod
    def _validate_question(question: str) -> None:
        question = question.strip()

        if not question:
            raise ValueError("Decision question cannot be empty.")

        if len(question) < 10:
            raise ValueError(
                "Please provide more details about your decision."
            )

    # ========================================================
    # OPTIONS
    # ========================================================

    @staticmethod
    def _validate_options(request: DecisionMakerRequest) -> None:
        options = request.options

        if len(options) < 2:
            raise ValueError(
                "Provide at least two options for comparison."
            )

        titles: Set[str] = set()

        for option in options:
            title = option.title.strip()

            if not title:
                raise ValueError(
                    "Option title cannot be empty."
                )

            normalized = title.lower()

            if normalized in titles:
                raise ValueError(
                    f"Duplicate option detected: '{title}'."
                )

            titles.add(normalized)

    # ========================================================
    # CRITERIA
    # ========================================================

    @staticmethod
    def _validate_criteria(request: DecisionMakerRequest) -> None:

        if request.criteria is None:
            return

        criteria = request.criteria

        if len(criteria.priorities) > 10:
            raise ValueError(
                "You can specify up to 10 priorities."
            )

        if len(criteria.constraints) > 10:
            raise ValueError(
                "You can specify up to 10 constraints."
            )

        for priority in criteria.priorities:
            if not priority.strip():
                raise ValueError(
                    "Priority values cannot be empty."
                )

        for constraint in criteria.constraints:
            if not constraint.strip():
                raise ValueError(
                    "Constraint values cannot be empty."
                )
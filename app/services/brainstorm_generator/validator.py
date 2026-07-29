"""
Brainstorm Generator Validator

Validates incoming BrainstormRequest before prompt generation.
"""

from app.models.brainstorm_generator import (
    BrainstormRequest,
)


class BrainstormValidator:
    """Validates Brainstorm Generator requests."""

    MIN_TOPIC_LENGTH = 3
    MAX_TOPIC_LENGTH = 300

    MIN_IDEA_COUNT = 3
    MAX_IDEA_COUNT = 20

    MAX_CONSTRAINTS = 10
    MAX_CONSTRAINT_LENGTH = 100

    MAX_GOAL_LENGTH = 300
    MAX_AUDIENCE_LENGTH = 200
    MAX_CONTEXT_LENGTH = 2000

    @classmethod
    def validate(cls, request: BrainstormRequest) -> None:
        """
        Validate complete brainstorm request.
        """

        cls._validate_topic(request.topic)
        cls._validate_idea_count(request.idea_count)
        cls._validate_criteria(request.criteria)

    @classmethod
    def _validate_topic(cls, topic: str) -> None:
        """
        Validate brainstorming topic.
        """

        if not topic:
            raise ValueError("Topic is required.")

        topic = topic.strip()

        if len(topic) < cls.MIN_TOPIC_LENGTH:
            raise ValueError(
                f"Topic must be at least {cls.MIN_TOPIC_LENGTH} characters."
            )

        if len(topic) > cls.MAX_TOPIC_LENGTH:
            raise ValueError(
                f"Topic cannot exceed {cls.MAX_TOPIC_LENGTH} characters."
            )

    @classmethod
    def _validate_idea_count(cls, count: int) -> None:
        """
        Validate requested number of ideas.
        """

        if count < cls.MIN_IDEA_COUNT:
            raise ValueError(
                f"Idea count must be at least {cls.MIN_IDEA_COUNT}."
            )

        if count > cls.MAX_IDEA_COUNT:
            raise ValueError(
                f"Idea count cannot exceed {cls.MAX_IDEA_COUNT}."
            )

    @classmethod
    def _validate_criteria(cls, criteria) -> None:
        """
        Validate optional brainstorming criteria.
        """

        if criteria.goal:
            if len(criteria.goal.strip()) > cls.MAX_GOAL_LENGTH:
                raise ValueError(
                    f"Goal cannot exceed {cls.MAX_GOAL_LENGTH} characters."
                )

        if criteria.target_audience:
            if len(criteria.target_audience.strip()) > cls.MAX_AUDIENCE_LENGTH:
                raise ValueError(
                    f"Target audience cannot exceed {cls.MAX_AUDIENCE_LENGTH} characters."
                )

        if criteria.additional_context:
            if len(criteria.additional_context.strip()) > cls.MAX_CONTEXT_LENGTH:
                raise ValueError(
                    f"Additional context cannot exceed {cls.MAX_CONTEXT_LENGTH} characters."
                )

        if len(criteria.constraints) > cls.MAX_CONSTRAINTS:
            raise ValueError(
                f"You can specify at most {cls.MAX_CONSTRAINTS} constraints."
            )

        seen = set()

        for constraint in criteria.constraints:

            if not constraint.strip():
                continue

            if len(constraint) > cls.MAX_CONSTRAINT_LENGTH:
                raise ValueError(
                    f"Constraint '{constraint}' exceeds "
                    f"{cls.MAX_CONSTRAINT_LENGTH} characters."
                )

            normalized = constraint.strip().lower()

            if normalized in seen:
                raise ValueError(
                    f"Duplicate constraint detected: '{constraint}'."
                )

            seen.add(normalized)
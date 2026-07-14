"""
ELI5 Validator
--------------
Validates business rules for ELI5 requests.
"""

from app.models.eli5 import ELI5Request


class ELI5Validator:
    """
    Business validation for ELI5 requests.
    """

    MIN_TOPIC_LENGTH = 3
    MAX_TOPIC_LENGTH = 500

    @classmethod
    def validate(cls, request: ELI5Request) -> None:
        """
        Validate an ELI5 request.

        Raises:
            ValueError: If the request violates business rules.
        """

        topic = request.topic.strip()

        if not topic:
            raise ValueError("Topic cannot be empty.")

        if len(topic) < cls.MIN_TOPIC_LENGTH:
            raise ValueError(
                f"Topic must contain at least {cls.MIN_TOPIC_LENGTH} characters."
            )

        if len(topic) > cls.MAX_TOPIC_LENGTH:
            raise ValueError(
                f"Topic cannot exceed {cls.MAX_TOPIC_LENGTH} characters."
            )
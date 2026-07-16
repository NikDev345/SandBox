"""
Email Studio Validator

Responsibilities
----------------
- Validate incoming requests.
- Validate according to the selected mode.
- Reject invalid or incomplete requests.
- Keep validation separate from business logic.

No AI logic.
No formatting.
No prompt generation.
"""

from __future__ import annotations

from app.models.email_rewriter import (
    EmailMode,
    EmailStudioRequest,
    EmailStudioResponse,
)


class EmailStudioValidator:
    """
    Validates Email Studio requests.

    Supported Modes

    - Rewrite
    - Generate
    """

    MAX_SUBJECT_LENGTH = 200

    MIN_TEXT_LENGTH = 10

    MAX_TEXT_LENGTH = 30_000

    @classmethod
    def validate(
        cls,
        request: EmailStudioRequest,
    ) -> None:

        cls._validate_subject(request.subject)

        if request.mode == EmailMode.REWRITE:
            cls._validate_rewrite(request)

        elif request.mode == EmailMode.GENERATE:
            cls._validate_generate(request)

        else:
            raise ValueError(
                "Unsupported email mode."
            )

    # ======================================================

    @classmethod
    def _validate_rewrite(
        cls,
        request: EmailStudioRequest,
    ) -> None:

        if not request.email:
            raise ValueError(
                "Email content is required for Rewrite mode."
            )

        cls._validate_text(
            request.email,
            "Email",
        )

    # ======================================================

    @classmethod
    def _validate_generate(
        cls,
        request: EmailStudioRequest,
    ) -> None:

        if not request.instruction:
            raise ValueError(
                "Instruction is required for Generate mode."
            )

        cls._validate_text(
            request.instruction,
            "Instruction",
        )

    # ======================================================

    @classmethod
    def _validate_subject(
        cls,
        subject: str | None,
    ) -> None:

        if subject is None:
            return

        if len(subject.strip()) > cls.MAX_SUBJECT_LENGTH:
            raise ValueError(
                f"Subject cannot exceed {cls.MAX_SUBJECT_LENGTH} characters."
            )

    # ======================================================

    @classmethod
    def _validate_text(
        cls,
        value: str,
        field_name: str,
    ) -> None:

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        if len(value) < cls.MIN_TEXT_LENGTH:
            raise ValueError(
                f"{field_name} must contain at least {cls.MIN_TEXT_LENGTH} characters."
            )

        if len(value) > cls.MAX_TEXT_LENGTH:
            raise ValueError(
                f"{field_name} exceeds the maximum allowed length."
            )

    # ======================================================

    @classmethod
    def extract_metadata(
        cls,
        request: EmailStudioRequest,
    ) -> dict:

        text = request.email or request.instruction or ""

        return {
            "mode": request.mode.value,
            "has_subject": bool(request.subject),
            "characters": len(text),
            "words": len(text.split()),
            "style": request.settings.style.value,
            "tone": request.settings.tone.value,
            "language": request.settings.language.value,
        }

    @classmethod
    def validate_response(
        cls,
        response: EmailStudioResponse,
    ) -> None:
        """
        Validate the formatted AI response.
        """

        if not response.full_email.strip():
            raise RuntimeError("AI response did not include email content.")

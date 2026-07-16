"""
Formatter for AI Email Studio.

Responsibilities
----------------
- Convert Gemini JSON into EmailStudioResponse.
- Apply safe defaults.
- Build full email if omitted.
- Keep parsing separate from business logic.

No Gemini calls.
No validation.
No prompt logic.
"""

from __future__ import annotations

from typing import Any

from app.models.email_rewriter import EmailStudioResponse


class EmailStudioFormatter:
    """
    Converts Gemini JSON into EmailStudioResponse.
    """

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @classmethod
    def format(
        cls,
        data: dict[str, Any],
    ) -> EmailStudioResponse:

        subject = cls._clean(data.get("subject"))

        greeting = cls._clean(data.get("greeting"))

        body = cls._clean(data.get("body"))

        closing = cls._clean(data.get("closing"))

        full_email = cls._clean(data.get("full_email"))

        suggestions = data.get("suggestions", [])

        if not isinstance(suggestions, list):
            suggestions = []

        suggestions = [
            cls._clean(item)
            for item in suggestions
            if cls._clean(item)
        ]

        if not full_email:

            sections = []

            if subject:
                sections.append(f"Subject: {subject}")

            if greeting:
                sections.append(greeting)

            if body:
                sections.append(body)

            if closing:
                sections.append(closing)

            full_email = "\n\n".join(sections)

        return EmailStudioResponse(
            subject=subject,
            greeting=greeting,
            body=body,
            closing=closing,
            full_email=full_email,
            suggestions=suggestions,
        )
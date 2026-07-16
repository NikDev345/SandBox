"""Service orchestration for the Email Rewriter backend."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from app.models.email_rewriter import (
    EmailMode,
    EmailStudioRequest,
    EmailStudioResponse,
)
from app.services.email_rewriter.formatter import EmailStudioFormatter
from app.services.email_rewriter.prompts import (
    GENERATE_SYSTEM_PROMPT,
    GENERATE_USER_PROMPT,
    REWRITE_SYSTEM_PROMPT,
    REWRITE_USER_PROMPT,
)
from app.services.email_rewriter.validator import EmailStudioValidator
from app.services.gemini_service import GeminiService


class EmailStudioService:
    """Run the Email Rewriter generation pipeline."""

    @classmethod
    async def generate(
        cls,
        request: EmailStudioRequest,
    ) -> EmailStudioResponse:
        """Generate or rewrite an email."""

        cleaned_request = cls._preprocess_input(request)
        prompt = cls._build_prompt(cleaned_request)
        raw_response = cls._generate_email(prompt)
        parsed_response = cls._parse_response(raw_response)
        response = EmailStudioFormatter.format(parsed_response)
        return cls._validate_response(response)

    @classmethod
    def _preprocess_input(
        cls,
        request: EmailStudioRequest,
    ) -> EmailStudioRequest:
        """Normalize request text and validate cleaned input."""

        cleaned_request = request.model_copy(deep=True)
        cleaned_request.subject = (
            cls._clean_text(cleaned_request.subject)
            if cleaned_request.subject
            else None
        )

        if cleaned_request.mode == EmailMode.REWRITE:
            cleaned_request.email = cls._clean_text(
                cleaned_request.email or ""
            )
            cleaned_request.instruction = (
                cls._clean_text(cleaned_request.instruction)
                if cleaned_request.instruction
                else None
            )

        elif cleaned_request.mode == EmailMode.GENERATE:
            cleaned_request.instruction = cls._clean_text(
                cleaned_request.instruction or ""
            )
            cleaned_request.email = (
                cls._clean_text(cleaned_request.email)
                if cleaned_request.email
                else None
            )

        EmailStudioValidator.validate(cleaned_request)
        return cleaned_request

    @staticmethod
    def _clean_text(text: str | None) -> str:
        """Normalize unicode, whitespace, line endings, and controls."""

        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)
        normalized = "".join(
            char
            for char in normalized
            if char in ("\n", "\t")
            or unicodedata.category(char)[0] != "C"
        )
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        lines = [line.strip() for line in normalized.split("\n")]
        cleaned_lines: list[str] = []
        previous_blank = False

        for line in lines:
            is_blank = line == ""
            if is_blank and previous_blank:
                continue

            cleaned_lines.append(line)
            previous_blank = is_blank

        normalized = "\n".join(cleaned_lines)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        return normalized.strip()

    @staticmethod
    def _build_prompt(request: EmailStudioRequest) -> str:
        """Build the Gemini prompt for the selected mode."""

        settings = request.settings

        if request.mode == EmailMode.REWRITE:
            user_prompt = REWRITE_USER_PROMPT.format(
                style=settings.style.value,
                tone=settings.tone.value,
                length=settings.length.value,
                language=settings.language.value,
                preserve_intent="yes" if settings.preserve_intent else "no",
                improve_subject="yes" if settings.improve_subject else "no",
                improve_greeting="yes" if settings.improve_greeting else "no",
                improve_closing="yes" if settings.improve_closing else "no",
                fix_grammar="yes" if settings.fix_grammar else "no",
                improve_clarity="yes" if settings.improve_clarity else "no",
                improve_readability=(
                    "yes" if settings.improve_readability else "no"
                ),
                subject=request.subject or "",
                email=request.email or "",
            )

            return (
                f"{REWRITE_SYSTEM_PROMPT.strip()}\n\n"
                f"{user_prompt.strip()}"
            )

        if request.mode == EmailMode.GENERATE:
            user_prompt = GENERATE_USER_PROMPT.format(
                instruction=request.instruction or "",
                style=settings.style.value,
                tone=settings.tone.value,
                length=settings.length.value,
                language=settings.language.value,
                subject=request.subject or "",
            )

            return (
                f"{GENERATE_SYSTEM_PROMPT.strip()}\n\n"
                f"{user_prompt.strip()}"
            )

        raise ValueError("Unsupported email mode.")

    @staticmethod
    def _generate_email(prompt: str) -> str:
        """Call Gemini to generate the raw email JSON string."""

        try:
            client = GeminiService()
            return client.generate(prompt)
        except Exception as exc:
            raise RuntimeError("Failed to generate email.") from exc

    @staticmethod
    def _parse_response(response: str) -> dict[str, Any]:
        """Parse Gemini JSON after removing optional markdown fences."""

        text = response.strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE)
            text = re.sub(r"```$", "", text).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI returned invalid JSON.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("AI response must be a JSON object.")

        return parsed

    @staticmethod
    def _validate_response(
        response: EmailStudioResponse,
    ) -> EmailStudioResponse:
        """Validate formatted AI response."""

        EmailStudioValidator.validate_response(response)
        return response

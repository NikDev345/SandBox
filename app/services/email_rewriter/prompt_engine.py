"""
Prompt Engine for AI Email Studio.

Responsibilities
----------------
- Select the correct prompt strategy.
- Build system prompt.
- Build user prompt.

No Gemini calls.
No formatting.
No validation.
"""

from __future__ import annotations

from typing import Callable

from app.models.email_rewriter import (
    EmailMode,
    EmailStudioRequest,
)

from app.services.email_rewriter.prompts import (
    REWRITE_SYSTEM_PROMPT,
    REWRITE_USER_PROMPT,
    GENERATE_SYSTEM_PROMPT,
    GENERATE_USER_PROMPT,
)


class PromptEngine:
    """
    Builds prompts for AI Email Studio.
    """

    # =====================================================
    # Rewrite
    # =====================================================

    @staticmethod
    def _rewrite_prompt(
        request: EmailStudioRequest,
    ) -> tuple[str, str]:

        settings = request.settings

        user_prompt = REWRITE_USER_PROMPT.format(
            style=settings.style.value,
            tone=settings.tone.value,
            length=settings.length.value,
            language=settings.language.value,
            preserve_intent="Yes" if settings.preserve_intent else "No",
            improve_subject="Yes" if settings.improve_subject else "No",
            improve_greeting="Yes" if settings.improve_greeting else "No",
            improve_closing="Yes" if settings.improve_closing else "No",
            fix_grammar="Yes" if settings.fix_grammar else "No",
            improve_clarity="Yes" if settings.improve_clarity else "No",
            improve_readability="Yes" if settings.improve_readability else "No",
            subject=request.subject or "No Subject",
            email=request.email or "",
        )

        return (
            REWRITE_SYSTEM_PROMPT.strip(),
            user_prompt.strip(),
        )

    # =====================================================
    # Generate
    # =====================================================

    @staticmethod
    def _generate_prompt(
        request: EmailStudioRequest,
    ) -> tuple[str, str]:

        settings = request.settings

        user_prompt = GENERATE_USER_PROMPT.format(
            instruction=request.instruction or "",
            style=settings.style.value,
            tone=settings.tone.value,
            length=settings.length.value,
            language=settings.language.value,
        )

        return (
            GENERATE_SYSTEM_PROMPT.strip(),
            user_prompt.strip(),
        )

    # =====================================================
    # Strategy Registry
    # =====================================================

    _BUILDERS: dict[
        EmailMode,
        Callable[[EmailStudioRequest], tuple[str, str]]
    ] = {
        EmailMode.REWRITE: _rewrite_prompt.__func__,
        EmailMode.GENERATE: _generate_prompt.__func__,
    }

    # =====================================================
    # Public API
    # =====================================================

    @classmethod
    def build(
        cls,
        request: EmailStudioRequest,
    ) -> tuple[str, str]:
        """
        Returns

        (
            system_prompt,
            user_prompt
        )
        """

        builder = cls._BUILDERS.get(request.mode)

        if builder is None:
            raise ValueError(
                f"Unsupported mode: {request.mode}"
            )

        return builder(request)
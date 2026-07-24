"""
============================================================
Decision Maker Service

Business logic for the Decision Maker AI tool.

Flow:
Request
    ↓
Validation
    ↓
Prompt Engine
    ↓
Gemini AI
    ↓
Formatter
    ↓
Structured Response

Author: Sandbox AI
============================================================
"""

import traceback

from fastapi import HTTPException
from sqlalchemy import exc

from app.models.decision_maker import (
    DecisionMakerRequest,
    DecisionMakerResponse,
)
from app.services.gemini_service import GeminiService
from app.services.decision_maker.formatter import (
    DecisionMakerFormatter,
)
from app.services.decision_maker.prompt_engine import PromptEngine
from app.services.decision_maker.validator import (
    DecisionMakerValidator,
)


class DecisionMakerService:
    """Decision Maker business logic."""

    @staticmethod
    async def analyze(
        request: DecisionMakerRequest,
    ) -> DecisionMakerResponse:
        """
        Analyze a user's decision using AI.

        Args:
            request: DecisionMakerRequest

        Returns:
            DecisionMakerResponse

        Raises:
            ValueError:
                Invalid user input.

            RuntimeError:
                AI processing failed.
        """

        # ----------------------------------------------------
        # Validate request
        # ----------------------------------------------------

        DecisionMakerValidator.validate(request)

        # ----------------------------------------------------
        # Build AI Prompt
        # ----------------------------------------------------

        prompt = PromptEngine.build_prompt(request)

        # ----------------------------------------------------
        # Generate AI Response
        # ----------------------------------------------------

        try:
            client = GeminiService()
            ai_response = client.generate(prompt)
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc
        return DecisionMakerFormatter.format(ai_response)

        # ----------------------------------------------------
        # Format Response
        # ----------------------------------------------------

        return DecisionMakerFormatter.format(
            ai_response
        )
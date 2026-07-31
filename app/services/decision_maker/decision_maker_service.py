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

import traceback, json

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
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
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService

class DecisionMakerService:
    """Decision Maker business logic."""

    @staticmethod
    async def analyze(
        request: DecisionMakerRequest,
        user_id: str,
        db: Session,
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
            tool = ToolService.get_tool_by_slug(
                    db=db,
                    slug="DECISION-MAKER",
                )
            tool_id = tool.id if tool else "DECISION-MAKER"
            ExecutionService.create_execution(
                    db=db,
                    user_id=user_id,
                    tool_id=tool_id,
                    user_input=request.model_dump_json(),
                    output=json.dumps(ai_response),
                )
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc
        return DecisionMakerFormatter.format(ai_response)

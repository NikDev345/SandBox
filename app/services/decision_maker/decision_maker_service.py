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
    DecisionLLMResponse
)
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
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
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)

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
            llm_response = await gateway.generate(
                LLMRequest(
                    prompt=prompt,
                    temperature=0.4,
                    max_output_tokens=2000,
                    tool_slug="decision_maker",
                    response_schema=DecisionLLMResponse
                )
            )
            
            if not llm_response or not llm_response.text:
                raise ValueError("Empty response from LLM")
    
            if not isinstance(llm_response.text, dict):
                raise ValueError("Invalid structured response")
    
            data = DecisionLLMResponse(**llm_response.text)
            
            tool = ToolService.get_tool_by_slug(
                    db=db,
                    slug="decision_maker",
                )
            tool_id = tool.id if tool else "decision_maker"
            execution_id = None
            execution = ExecutionService.create_execution(
                    db=db,
                    user_id=user_id,
                    tool_id=tool_id,
                    user_input=request.model_dump_json(),
                    output=json.dumps(data.model_dump())
                )
            execution_id = execution.id
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc
            
        response = DecisionMakerResponse(
            success=True,
            summary=data.summary,
            recommendation=data.recommendation,
            analysis=data.analysis,
            key_factors=data.key_factors,
            final_advice=data.final_advice,
            disclaimer=data.disclaimer,
            execution_id=execution_id
        )
        return response

"""
Brainstorm Generator Service

Flow:
    Validate
        ↓
    Build Prompt
        ↓
    Gemini
        ↓
    Formatter
        ↓
    Response
"""

from app.models.brainstorm_generator import (
    BrainstormRequest,
    BrainstormResponse,
)
from app.services.brainstorm_generator.validator import (
    BrainstormValidator,
)
from app.services.brainstorm_generator.prompt_engine import (
    BrainstormPromptEngine,
)
from app.services.brainstorm_generator.formatter import (
    BrainstormFormatter,
)
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
from sqlalchemy.orm import Session
import json

class BrainstormGeneratorService:
    """Service responsible for generating AI-powered brainstorming ideas."""

    @staticmethod
    async def generate(request: BrainstormRequest, user_id: str, db: Session) -> BrainstormResponse:
        """
        Generate brainstorming ideas.

        Flow:
            1. Validate request
            2. Build AI prompt
            3. Generate response using Gemini
            4. Parse & validate response
            5. Return structured response
        """

        # Step 1: Validate request
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)
        BrainstormValidator.validate(request)

        # Step 2: Build prompt
        prompt = BrainstormPromptEngine.build_prompt(request)

        # Step 3: Generate response from Gemini
        raw_response = await gateway.generate(LLMRequest(
            prompt=prompt,
            tool_slug="brainstorm_generator",
            temperature=0.5,
        ))

        if raw_response is None:
            raise ValueError("Gemini returned no response.")

        if not raw_response or not raw_response.text or not raw_response.text.strip():
            raise ValueError("Gemini returned an empty response.")

        # Step 4: Format & validate response
        response = BrainstormFormatter.format(raw_response.text)
        user_input = request.model_dump_json()
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="brainstorm_generator",
            )
        tool_id = tool.id if tool else "brainstorm_generator"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=user_input,
                output=json.dumps(response.model_dump()) if hasattr(response, 'model_dump') else str(response),
            )
            execution_id = execution.id if execution else None
        except Exception:
                pass
        

        # Step 5: Return structured response
        response.execution_id = execution_id
        return response
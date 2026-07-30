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
from app.services.gemini_service import GeminiService
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
from sqlalchemy.orm import Session

class BrainstormGeneratorService:
    """Service responsible for generating AI-powered brainstorming ideas."""

    @staticmethod
    def generate(request: BrainstormRequest, user_id: str, db: Session) -> BrainstormResponse:
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
        BrainstormValidator.validate(request)

        # Step 2: Build prompt
        prompt = BrainstormPromptEngine.build_prompt(request)

        # Step 3: Generate response from Gemini
        gemini = GeminiService()
        raw_response = gemini.generate(prompt)

        if raw_response is None:
            raise ValueError("Gemini returned no response.")

        if isinstance(raw_response, str) and not raw_response.strip():
            raise ValueError("Gemini returned an empty response.")

        # Step 4: Format & validate response
        response = BrainstormFormatter.format(raw_response)
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="JSON-FIXER",
            )
        tool_id = tool.id if tool else "JSON-FIXER"
        
        try:
            ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=request.topic,
            output=response,
        )
        except Exception:
                pass
        

        # Step 5: Return structured response
        return response
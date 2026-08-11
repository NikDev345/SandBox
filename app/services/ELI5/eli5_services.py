"""
ELI5 Service
------------
Coordinates the complete ELI5 explanation workflow.
"""

from app.models.eli5 import ELI5Request, ELI5Response
from app.services.ELI5.prompt_engine import PromptEngine
from app.services.ELI5.validator import ELI5Validator
from app.services.ELI5.formatter import ELI5Formatter
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
from app.utils.eli5 import normalize_topic
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class ELI5Service:
    """
    Orchestrates the ELI5 explanation workflow.
    """

    async def generate_explanation(
        self,
        request: ELI5Request,
        db: Session,
        user=None,
    ) -> ELI5Response:
        """
        Generate an ELI5 explanation.

        Args:
            request: User request.
            user: Authenticated user.

        Returns:
            ELI5Response
        """

        # Validate request
        ELI5Validator.validate(request)

        # Normalize topic
        request.topic = normalize_topic(request.topic)

        # Build prompt
        prompt = PromptEngine.build_prompt(request)

        # Generate explanation
        llm_request = LLMRequest(
            prompt=prompt,
            temperature=0.6,        # slightly higher for ELI5 creativity
            max_tokens=1500,
            response_schema="text",
            tool_slug="eli5",
        )

        response1 = await gateway.generate(llm_request)

        if not response1 or not response1.output:
            raise RuntimeError("Empty response from LLM Gateway")

        explanation = response1.output
        
        tool = ToolService.get_tool_by_slug(
                    db=db,
                    slug="eli5",
                )
        tool_id = tool.id if tool else "eli5"
        execution_record = None
        try:
            execution_record = ExecutionService.create_execution(
                db=db,
                user_id=user["sub"],
                tool_id=tool_id,
                user_input=request.model_dump_json(),
                output=explanation,
            )
        except Exception:
            pass

        # Format response
        response = ELI5Formatter.format(explanation)
        response.execution_id = execution_record.id if execution_record else None
        return response
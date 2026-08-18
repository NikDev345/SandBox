import json
from app.models.chart_explainer import (
    ChartExplainerRequest,
    ChartExplainerResponse,
    ChartExplainerLLMResponse
)
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
from app.services.prompt_engine import PromptEngine
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class ChartExplainerService:
    """
    Service responsible for analyzing chart images using Gemini Vision.
    """

    def __init__(self):
        self.gateway = gateway

    async def analyze(
        self,
        request: ChartExplainerRequest,
        image_bytes: bytes,
        mime_type: str,
        user_id: str,
        db: Session,
    ) -> ChartExplainerResponse:
        """
        Analyze the uploaded chart image.
        """
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)
        prompt = PromptEngine.build_chart_explainer_prompt(request)
        contents = [
            {
                "type": "image",
                "data": image_bytes,
                "mime_type": mime_type
            }
        ]
        llm_response = await self.gateway.generate(
            LLMRequest(
                prompt=prompt,
                contents=contents,
                tool_slug="chart_explainer",
                temperature=0.2,
                response_schema=ChartExplainerLLMResponse
            )
        )
        if not llm_response or not llm_response.text:
            raise ValueError("LLM returned empty response")

        if not isinstance(llm_response.text, dict):
            raise ValueError("Invalid structured response from LLM")
                
        user_input = json.dumps({
            "mime_type": mime_type,
            "filename": request.filename if hasattr(request, "filename") else None,
            "prompt_options": request.model_dump() if hasattr(request, "model_dump") else {}
        })
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="chart_explainer",
            )
        tool_id = tool.id if tool else "chart_explainer"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=user_input,
                output=json.dumps(llm_response.text),
            )
            execution_id = execution.id
        except Exception:
            pass

        response = ChartExplainerResponse(
            **llm_response.text,
            execution_id=execution_id
        )
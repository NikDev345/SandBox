from google.genai import types
import json
from app.models.chart_explainer import (
    ChartExplainerRequest,
    ChartExplainerResponse,
)
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
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

        uploaded_image = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        result = await self.gateway.generate(
            LLMRequest(
                prompt=prompt,
                contents=[uploaded_image],
                tool_slug="chart_explainer",
                temperature=0.2,
                response_mime_type="application/json",
            )
        )
        
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
                output=str(result),
            )
            execution_id = execution.id
        except Exception:
            pass

        return ChartExplainerResponse(
            chart_type=result.get("chart_type", ""),
            executive_summary=result.get("executive_summary", ""),
            axis_explanation=result.get("axis_explanation", ""),
            key_insights=result.get("key_insights", []),
            trend_analysis=result.get("trend_analysis", ""),
            outliers=result.get("outliers", []),
            business_insights=result.get("business_insights", ""),
            recommendations=result.get("recommendations", []),
            questions_answered=result.get("questions_answered", []),
            limitations=result.get("limitations", []),
            eli5_explanation=result.get("eli5_explanation", ""),
            confidence_score=result.get("confidence_score", 0),
            execution_id=execution_id,
            usage=result.get("usage"),
        )
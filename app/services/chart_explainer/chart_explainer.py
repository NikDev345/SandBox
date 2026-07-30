from google.genai import types
import json
from app.models.chart_explainer import (
    ChartExplainerRequest,
    ChartExplainerResponse,
)
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class ChartExplainerService:
    """
    Service responsible for analyzing chart images using Gemini Vision.
    """

    def __init__(self):
        self.gemini = GeminiService()

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

        prompt = PromptEngine.build_chart_explainer_prompt(request)

        uploaded_image = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        result = await self.gemini.generate_image_json(
            uploaded_image=uploaded_image,
            prompt=prompt,
        )
        user_input = json.dumps({
            "mime_type": mime_type,
            "filename": request.filename if hasattr(request, "filename") else None,
            "prompt_options": request.model_dump() if hasattr(request, "model_dump") else {}
        })
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="CHART-EXPLAINER",
            )
        tool_id = tool.id if tool else "CHART-EXPLAINER"
        
        try:
            ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=user_input,
                output=str(result),
            )
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
            usage=result.get("usage"),
        )
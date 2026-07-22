from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.utils.auth import get_current_user
from app.models.chart_explainer import (
    ChartExplainerRequest,
    ChartExplainerResponse,
    ExplanationLevel,
    OutputLanguage,
)
from app.models.user import Users
from app.services.chart_explainer.chart_explainer import ChartExplainerService

router = APIRouter(
    prefix="/chart-explainer",
    tags=["Chart Explainer"],
)

service = ChartExplainerService()


@router.post(
    "/analyze",
    response_model=ChartExplainerResponse,
    summary="Analyze a chart image using AI",
)
async def analyze_chart(
    image: UploadFile = File(...),

    language: OutputLanguage = Form(OutputLanguage.ENGLISH),
    explanation_level: ExplanationLevel = Form(
        ExplanationLevel.INTERMEDIATE
    ),

    include_summary: bool = Form(True),
    include_axis_explanation: bool = Form(True),
    include_key_insights: bool = Form(True),
    include_trend_analysis: bool = Form(True),
    include_outliers: bool = Form(True),
    include_business_insights: bool = Form(True),
    include_recommendations: bool = Form(True),
    include_questions_answered: bool = Form(True),
    include_limitations: bool = Form(True),
    include_eli5: bool = Form(True),
    include_confidence: bool = Form(True),

    current_user: Users = Depends(get_current_user),
):
    """
    Analyze an uploaded chart image.
    """

    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are supported.",
        )

    image_bytes = await image.read()

    request = ChartExplainerRequest(
        language=language,
        explanation_level=explanation_level,
        include_summary=include_summary,
        include_axis_explanation=include_axis_explanation,
        include_key_insights=include_key_insights,
        include_trend_analysis=include_trend_analysis,
        include_outliers=include_outliers,
        include_business_insights=include_business_insights,
        include_recommendations=include_recommendations,
        include_questions_answered=include_questions_answered,
        include_limitations=include_limitations,
        include_eli5=include_eli5,
        include_confidence=include_confidence,
    )

    return await service.analyze(
        request=request,
        image_bytes=image_bytes,
        mime_type=image.content_type,
    )
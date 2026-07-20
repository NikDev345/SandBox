from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OutputLanguage(str, Enum):
    ENGLISH = "English"
    HINDI = "Hindi"


class ExplanationLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class ChartExplainerRequest(BaseModel):
    language: OutputLanguage = OutputLanguage.ENGLISH
    explanation_level: ExplanationLevel = ExplanationLevel.INTERMEDIATE

    include_summary: bool = True
    include_axis_explanation: bool = True
    include_key_insights: bool = True
    include_trend_analysis: bool = True
    include_outliers: bool = True
    include_business_insights: bool = True
    include_recommendations: bool = True
    include_questions_answered: bool = True
    include_limitations: bool = True
    include_eli5: bool = True
    include_confidence: bool = True

class AxisExplanation(BaseModel):
    x_axis: str
    y_axis: str
    units: str
    legend: str

class ChartExplainerResponse(BaseModel):
    chart_type: str
    executive_summary: str

    axis_explanation: AxisExplanation

    key_insights: List[str]
    trend_analysis: List[str]
    outliers: List[str]
    business_insights: List[str]
    recommendations: List[str]
    questions_answered: List[str]
    limitations: List[str]

    eli5_explanation: str
    confidence_score: int

    usage: Optional[dict] = None
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalysisDepth(str, Enum):
    QUICK = "quick"
    BALANCED = "balanced"
    DETAILED = "detailed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =====================================================
# Request
# =====================================================

class ProConsRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Decision, product or topic to analyze."
    )

    context: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Additional information provided by the user."
    )

    analysis_depth: AnalysisDepth = AnalysisDepth.BALANCED


# =====================================================
# Response
# =====================================================

class ComparisonItem(BaseModel):
    title: str
    description: str
    impact: RiskLevel = RiskLevel.MEDIUM  

class Recommendation(BaseModel):
    recommendation: str
    summary: str
    verdict: str
    risk_level: RiskLevel
    confidence_score: int = Field(ge=0, le=100)


class ProConsResponse(BaseModel):
    topic: str
    summary: str
    pros: List[ComparisonItem]
    cons: List[ComparisonItem]
    recommendation: Recommendation
    generated_at: datetime
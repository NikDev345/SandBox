"""
============================================================
Decision Maker Models

Defines all request and response schemas for the Decision
Maker AI tool.

Author: Sandbox AI
============================================================
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================

class DecisionType(str, Enum):
    """Supported decision categories."""

    PERSONAL = "personal"
    CAREER = "career"
    EDUCATION = "education"
    BUSINESS = "business"
    FINANCIAL = "financial"
    HEALTH = "health"
    TECHNOLOGY = "technology"
    PURCHASE = "purchase"
    RELATIONSHIP = "relationship"
    CUSTOM = "custom"


# ============================================================
# REQUEST MODELS
# ============================================================

class DecisionOption(BaseModel):
    """A single option the user is considering."""

    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(
        default=None,
        max_length=1000
    )


class DecisionCriteria(BaseModel):
    """Optional criteria to influence AI analysis."""

    budget: Optional[str] = None
    timeline: Optional[str] = None
    priorities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    additional_context: Optional[str] = None


class DecisionMakerRequest(BaseModel):
    """Incoming request."""

    question: str = Field(
        ...,
        min_length=10,
        max_length=2000
    )

    decision_type: DecisionType = DecisionType.CUSTOM

    options: List[DecisionOption] = Field(
        ...,
        min_length=2,
        max_length=10
    )

    criteria: Optional[DecisionCriteria] = None


# ============================================================
# RESPONSE MODELS
# ============================================================

class DecisionRecommendation(BaseModel):
    """AI's recommended option."""

    selected_option: str
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str


class DecisionAnalysis(BaseModel):
    """Analysis for each available option."""

    option: str
    pros: List[str]
    cons: List[str]
    risks: List[str]
    score: float


class DecisionMakerResponse(BaseModel):
    """Final API response."""

    success: bool

    summary: str

    recommendation: DecisionRecommendation

    analysis: List[DecisionAnalysis]

    key_factors: List[str]

    final_advice: str

    disclaimer: str
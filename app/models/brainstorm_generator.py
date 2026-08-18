from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

class BrainstormCategory(str, Enum):
    BUSINESS = "business"
    STARTUP = "startup"
    PRODUCT = "product"
    MARKETING = "marketing"
    CONTENT = "content"
    SOCIAL_MEDIA = "social_media"
    BLOG = "blog"
    YOUTUBE = "youtube"
    APP = "app"
    WEBSITE = "website"
    AI = "ai"
    MACHINE_LEARNING = "machine_learning"
    RESEARCH = "research"
    EDUCATION = "education"
    EVENT = "event"
    CREATIVE_WRITING = "creative_writing"
    PROBLEM_SOLVING = "problem_solving"
    PERSONAL = "personal"
    GENERAL = "general"


class CreativityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BrainstormIdea(BaseModel):
    title: str = Field(..., description="Idea title")
    description: str = Field(..., description="Detailed explanation")
    why_it_works: str = Field(..., description="Reason this idea is effective")
    difficulty: str = Field(..., description="Easy, Medium or Hard")
    innovation_score: float = Field(
        ..., ge=0, le=10,
        description="Innovation score out of 10"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Suggested implementation steps"
    )


class BrainstormCriteria(BaseModel):
    goal: Optional[str] = None
    target_audience: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    additional_context: Optional[str] = None


class BrainstormRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        max_length=300
    )

    category: BrainstormCategory = BrainstormCategory.GENERAL

    creativity: CreativityLevel = CreativityLevel.MEDIUM

    idea_count: int = Field(
        default=10,
        ge=3,
        le=20
    )

    criteria: BrainstormCriteria = Field(
        default_factory=BrainstormCriteria
    )


class BrainstormResponse(BaseModel):
    success: bool

    summary: str

    ideas: List[BrainstormIdea]

    best_idea: str

    implementation_tips: List[str]

    common_mistakes: List[str]

    final_recommendation: str
    
    execution_id: Optional[str] = None
    
class BrainstormLLMResponse(BaseModel):
    success: bool
    summary: str
    ideas: List[BrainstormIdea]
    best_idea: str
    implementation_tips: List[str]
    common_mistakes: List[str]
    final_recommendation: str
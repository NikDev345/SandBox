from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BlogGoal(str, Enum):
    EDUCATE = "Educate"
    INFORM = "Inform"
    GUIDE = "Guide"
    TUTORIAL = "Tutorial"
    COMPARISON = "Comparison"
    REVIEW = "Review"
    OPINION = "Opinion"
    CASE_STUDY = "Case Study"
    LISTICLE = "Listicle"
    PRODUCT_PROMOTION = "Product Promotion"
    SEO = "SEO Content"


class BlogTone(str, Enum):
    PROFESSIONAL = "Professional"
    FRIENDLY = "Friendly"
    CONVERSATIONAL = "Conversational"
    FORMAL = "Formal"
    CASUAL = "Casual"
    TECHNICAL = "Technical"
    PERSUASIVE = "Persuasive"
    STORYTELLING = "Storytelling"
    INSPIRATIONAL = "Inspirational"


class OutlineDepth(str, Enum):
    BASIC = "Basic"
    STANDARD = "Standard"
    DETAILED = "Detailed"
    COMPREHENSIVE = "Comprehensive"


class TargetAudience(str, Enum):
    GENERAL = "General Readers"
    BEGINNER = "Beginners"
    INTERMEDIATE = "Intermediate"
    EXPERT = "Experts"
    STUDENTS = "Students"
    PROFESSIONALS = "Professionals"
    BUSINESS = "Business Owners"
    DEVELOPERS = "Developers"
    RESEARCHERS = "Researchers"
    CUSTOM = "Custom"


class Language(str, Enum):
    ENGLISH = "English"
    HINDI = "Hindi"
    GUJARATI = "Gujarati"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"


class BlogOutlineRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300)

    audience: TargetAudience = TargetAudience.GENERAL

    goal: BlogGoal = BlogGoal.EDUCATE

    tone: BlogTone = BlogTone.PROFESSIONAL

    depth: OutlineDepth = OutlineDepth.STANDARD

    sections: int = Field(
        default=6,
        ge=3,
        le=15
    )

    language: Language = Language.ENGLISH

    include_introduction: bool = True

    include_conclusion: bool = True

    include_faqs: bool = True

    include_cta: bool = True

    include_statistics: bool = True

    include_examples: bool = True

    include_case_studies: bool = False

    include_internal_links: bool = True

    include_external_resources: bool = True

    include_key_takeaways: bool = True

    primary_keyword: Optional[str] = None

    secondary_keywords: List[str] = Field(default_factory=list)


class BlogOutlineResponse(BaseModel):
    outline: str

    usage: Optional[dict] = None

    model_config = {
        "from_attributes": True
    }
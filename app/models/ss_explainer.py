from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class ExplanationAction(str, Enum):
    GENERAL_EXPLANATION = "general_explanation"
    QUICK_SUMMARY = "quick_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    STEP_BY_STEP_WALKTHROUGH = "step_by_step_walkthrough"
    ERROR_ANALYSIS = "error_analysis"
    TEXT_EXTRACTION = "text_extraction"
    UI_UX_REVIEW = "ui_ux_review"
    ACCESSIBILITY_REVIEW = "accessibility_review"
    EDUCATIONAL_EXPLANATION = "educational_explanation"
    TROUBLESHOOTING = "troubleshooting"
    OTHER = "other"

class ScreenshotExplainerRequest(BaseModel):
    action: ExplanationAction = Field(
        ...,
        description="Selected explanation action."
    )

    custom_action: Optional[str] = Field(
        default=None,
        max_length=1700,  # ~200 words
        description="Required only when action is OTHER."
    )
    
class ScreenshotExplainerResponse(BaseModel):
    title: str
    explanation: str
    
class ScreenshotMetadata(BaseModel):
    filename: str
    content_type: str
    file_size: int
    width: int
    height: int
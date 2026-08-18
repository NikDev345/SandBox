from enum import Enum
from pydantic import BaseModel, Field, model_validator
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
    
    @model_validator(mode="after")
    def validate_custom_action(self):
        if self.action == ExplanationAction.OTHER and not self.custom_action:
            raise ValueError("custom_action is required when action is OTHER")

        if self.action != ExplanationAction.OTHER and self.custom_action:
            raise ValueError("custom_action should only be provided when action is OTHER")

        return self
    
class ScreenshotExplainerResponse(BaseModel):
    title: str
    explanation: str
    execution_id: Optional[str] = None
    
class ScreenshotMetadata(BaseModel):
    filename: str
    content_type: str
    file_size: int
    width: int
    height: int
    
class ScreenshotExplainerLLMResponse(BaseModel):
    title: str
    explanation: str
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator, computed_field

# ----------------------------
# Request Model
# ----------------------------

class ActionItemExtractorRequest(BaseModel):
    """
    Input for Action Item Extractor.
    Exactly one of text or file_path should be provided.
    """

    text: Optional[str] = Field(
        default=None,
        description="Plain text input."
    )

    file_path: Optional[str] = Field(
        default=None,
        description="Path to PDF, DOCX, or TXT file."
    )
    @model_validator(mode="after")
    def validate_input(self):
        if not self.text and not self.file_path:
            raise ValueError("Either text or file_path must be provided")

        if self.text and self.file_path:
            raise ValueError("Provide only one of text or file_path")

        return self


# ----------------------------
# Response Models
# ----------------------------

class ActionItem(BaseModel):
    """
    Single extracted action item.
    """

    task: str = Field(
        description="The action that needs to be completed."
    )

    assignee: Optional[str] = Field(
        default=None,
        description="Person responsible for the task."
    )

    deadline: Optional[str] = Field(
        default=None,
        description="Mentioned deadline or due date."
    )
    @model_validator(mode="after")
    def clean_fields(self):
        self.task = self.task.strip()

        if not self.task:
            raise ValueError("Task cannot be empty")

        if self.assignee:
            self.assignee = self.assignee.strip() or None

        if self.deadline:
            self.deadline = self.deadline.strip() or None

        return self



class ActionItemExtractorResponse(BaseModel):
    action_items: List[ActionItem] = Field(default_factory=list)
    execution_id: Optional[str] = None

    @computed_field
    @property
    def total_action_items(self) -> int:
        return len(self.action_items)
    
class ActionItemLLM(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None


class ActionItemExtractorLLMResponse(BaseModel):
    action_items: List[ActionItemLLM]
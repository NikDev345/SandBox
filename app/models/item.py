from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


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


class ActionItemExtractorResponse(BaseModel):
    """
    Response returned by the extractor.
    """

    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="List of extracted action items."
    )

    total_action_items: int = Field(
        default=0,
        description="Total number of extracted tasks."
    )
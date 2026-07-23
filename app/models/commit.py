from pydantic import BaseModel, Field
from typing import Literal, List


class CommitMessageRequest(BaseModel):
    repository_path: str = Field(
        ...,
        description="Absolute path to the Git repository."
    )

    diff_type: Literal[
        "auto",
        "staged",
        "unstaged"
    ] = Field(
        default="auto",
        description="Which Git diff to analyze."
    )

    style: Literal[
        "conventional",
        "normal",
        "emoji"
    ] = Field(
        default="conventional",
        description="Commit message style."
    )

    suggestions: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of commit message suggestions."
    )
    
    
class CommitSuggestion(BaseModel):
    message: str

class CommitMessageResponse(BaseModel):
    repository_name: str
    branch: str

    diff_type: str

    files_changed: int

    suggestions: List[CommitSuggestion]

class GitData(BaseModel):
    repository_name: str
    branch: str

    diff_type: Literal[
        "staged",
        "unstaged"
    ]

    changed_files: List[str]

    diff: str
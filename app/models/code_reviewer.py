from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List


class ReviewInputType(str, Enum):
    SNIPPET = "snippet"
    FILE = "file"

class ProgrammingLanguage(str, Enum):
    AUTO = "auto"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    RUST = "rust"
    
class CodeReviewRequest(BaseModel):
    input_type: ReviewInputType = Field(
        description="Whether the input is a pasted code snippet or an uploaded file."
    )

    language: ProgrammingLanguage = Field(
        default=ProgrammingLanguage.AUTO,
        description="Programming language. Auto-detected for uploaded files."
    )

    code: Optional[str] = Field(
        default=None,
        description="Code snippet when input_type='snippet'."
    )
    
    
class ReviewIssue(BaseModel):
    title: str
    description: str

class ReviewSuggestion(BaseModel):
    title: str
    description: str

class CyclomaticComplexity(BaseModel):
    maximum: int
    average: float

class CodeReviewResponse(BaseModel):
    language: str
    lines_of_code: int
    file_size: float
    cyclomatic_complexity: CyclomaticComplexity
    time_complexity: str
    space_complexity: str
    summary: str
    errors: List[ReviewIssue]
    suggestions: List[ReviewSuggestion]
    execution_id: Optional[str] = None
    
class AIReviewResult(BaseModel):
    """Represents only the fields the AI returns — used internally by _parse_ai_review."""
    summary: str
    time_complexity: str
    space_complexity: str
    errors: List[ReviewIssue]
    suggestions: List[ReviewSuggestion]
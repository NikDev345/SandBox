from pydantic import BaseModel, Field, field_validator
from typing import List

class IssueGroup(BaseModel):
    critical: List[str]
    high: List[str]
    medium: List[str]
    low: List[str]

class ReviewScore(BaseModel):
    overall: int
    correctness: int
    security: int
    performance: int
    maintainability: int
    readability: int
    
class CodeReview(BaseModel):

    language: str
    review_type: str
    quality: str
    estimated_complexity: str
    lines_of_code: int
    score: ReviewScore
    summary: str
    issues: IssueGroup
    security: str
    performance: str
    best_practices: str
    suggestions: List[str]
    improved_code: str
    verdict: str

class CodeReviewerRequest(BaseModel):
    '''
    request schema for code reviewer tool
    '''
    
    code: str = Field(..., description="Source code to review")
    language: str = Field(..., description="Programming Language")
    input_type: str = Field(..., default=None)
    filename: str = Field(..., default=None)
    files: list = Field(..., None)
    zip_path: str = Field(..., None)
    review_type: str = Field(..., description="Type of review")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str):
        if not value.strip():
            raise ValueError("Code cannot be empty")
        return value
    
class CodeReviewerResponse(BaseModel):
    review: CodeReview
    
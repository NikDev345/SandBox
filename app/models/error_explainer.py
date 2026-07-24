from pydantic import BaseModel, Field
from typing import Optional, List


class ErrorExplainerRequest(BaseModel):
    error: str = Field(
        ...,
        description="Complete error message, stack trace, or log to explain."
    )

    code: Optional[str] = Field(
        default=None,
        description="Optional source code related to the error."
    )

    
class ErrorExplainerResponse(BaseModel):
    title: str = Field(
        ...,
        description="Short title of the error."
    )

    explanation: str = Field(
        ...,
        description="Human-readable explanation of the error."
    )

    code: Optional[str] = Field(
        default=None,
        description="Corrected code, command, or configuration snippet if applicable."
    )
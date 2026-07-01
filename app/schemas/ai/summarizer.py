from typing import Literal

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """
    Request schema for AI Text Summarizer.
    """

    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Text to summarize."
    )

    length: Literal["short", "medium", "detailed"] = Field(
        default="medium",
        description="Desired summary length."
    )


class SummarizeResponse(BaseModel):
    """
    Response schema for AI Text Summarizer.
    """

    summary: str = Field(
        ...,
        description="Generated summary."
    )   
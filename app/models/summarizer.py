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
    instructions: str | None = Field(
        default=None,
        description="Optional user instructions for the summary."
    )


class SummarizeResponse(BaseModel):
    """
    Response schema for AI Text Summarizer.
    """

    summary: str = Field(
        ...,
        description="Generated summary."
    )   


class ExtractResponse(BaseModel):
    """
    Response schema for extracted document text.
    """

    text: str = Field(..., description="Extracted text from uploaded document.")


class DownloadRequest(BaseModel):
    """
    Request schema for PDF download of summary.
    """

    summary: str = Field(..., description="Summary text to render as PDF.")
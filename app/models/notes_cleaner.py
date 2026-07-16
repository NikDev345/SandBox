from typing import Optional

from pydantic import BaseModel, Field


class NotesCleanerRequest(BaseModel):
    text: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1_000_000,
        description="Notes entered directly by the user. Leave empty when uploading a document."
    )


class DocumentMetadata(BaseModel):
    filename: str = Field(
        ...,
        description="Original name of the uploaded document."
    )

    content_type: str = Field(
        ...,
        description="MIME type of the uploaded document."
    )

    file_size: int = Field(
        ...,
        ge=0,
        description="Size of the uploaded document in bytes."
    )

    page_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of pages for supported document types (e.g. PDF)."
    )


class NotesCleanerResponse(BaseModel):
    title: str = Field(
        ...,
        description="Short title describing the cleaned notes."
    )

    cleaned_notes: str = Field(
        ...,
        description="The cleaned, formatted, and readable version of the user's notes."
    )
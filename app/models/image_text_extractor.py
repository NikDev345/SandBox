from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class OCRStatistics(BaseModel):
    characters: int = Field(..., ge=0)
    words: int = Field(..., ge=0)
    lines: int = Field(..., ge=0)
    paragraphs: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0, le=100)
    processing_time: float = Field(..., ge=0)


class OCRResult(BaseModel):
    filename: str
    language: str
    extracted_text: str
    statistics: OCRStatistics
    warnings: List[str] = Field(default_factory=list)


class ImageTextExtractorRequest(BaseModel):
    """
    Metadata request for Image Text Extractor.
    Image file itself is received through FastAPI UploadFile.
    """

    language: Optional[str] = Field(
        default="auto",
        description="OCR language"
    )

    preserve_layout: bool = Field(
        default=True,
        description="Keep original layout"
    )

    enhance_image: bool = Field(
        default=True,
        description="Apply preprocessing before OCR"
    )

    output_format: str = Field(
        default="text",
        description="Output format"
    )

    @field_validator("output_format")
    @classmethod
    def validate_output(cls, value: str):

        allowed = {
            "text",
            "json",
            "markdown"
        }

        value = value.lower()

        if value not in allowed:
            raise ValueError(
                f"Output format must be one of {allowed}"
            )

        return value


class ImageTextExtractorResponse(BaseModel):
    success: bool
    message: str
    result: OCRResult
"""
Table Extractor Models

Pydantic models used by the Table Extractor API.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class TableCell(BaseModel):
    """
    Represents a single cell in a table.
    """

    row: int = Field(..., ge=0)
    column: int = Field(..., ge=0)
    text: str = ""
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class TableRow(BaseModel):
    """
    Represents one row of a table.
    """

    cells: List[str]


class TableInfo(BaseModel):
    """
    Metadata and extracted content for a single table.
    """

    table_index: int
    page: int

    rows: int
    columns: int

    headers: List[str] = Field(default_factory=list)

    data: List[List[str]] = Field(default_factory=list)

    average_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


class TableExtractorRequest(BaseModel):
    """
    API request body (used for metadata only).
    The uploaded file is handled separately through FastAPI UploadFile.
    """

    output_format: OutputFormat = OutputFormat.EXCEL


class TableExtractorResponse(BaseModel):
    """
    API response returned after extraction.
    """

    success: bool

    filename: str

    pages_processed: int

    tables_found: int

    output_format: OutputFormat

    tables: List[TableInfo] = Field(default_factory=list)

    download_file: Optional[str] = None

    processing_time: float

    message: str
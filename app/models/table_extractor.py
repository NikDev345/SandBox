"""
Table Extractor Models

Strongly typed dataclasses used internally by TableExtractor to replace
anonymous dictionaries for page results and API responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PIL import Image


@dataclass(frozen=True)
class OcrResult:
    """
    Normalized OCR output for a single page.

    ``data`` is an already-normalized, parser-ready dictionary.
    ``item_count`` is supplied by the OCR service itself so the extractor
    never has to inspect prediction field names.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    item_count: int = 0


@dataclass(frozen=True)
class PageResult:
    """Result of running table detection and OCR on a single page."""

    page_number: int
    image: Image.Image
    table_predictions: List[Dict[str, Any]] = field(default_factory=list)
    ocr_result: OcrResult = field(default_factory=OcrResult)


@dataclass(frozen=True)
class ExtractionStatistics:
    """Aggregate statistics for a completed extraction run."""

    pages: int
    tables: int
    processing_time: float
    ocr_items: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pages": self.pages,
            "tables": self.tables,
            "processing_time": self.processing_time,
            "ocr_items": self.ocr_items,
        }


@dataclass(frozen=True)
class ExtractionMetadata:
    """Metadata describing how a response was produced."""

    format: str
    version: str

    def to_dict(self) -> Dict[str, Any]:
        return {"format": self.format, "version": self.version}


@dataclass(frozen=True)
class ExtractionResponse:
    """Final structured response returned by TableExtractor.extract()."""

    success: bool
    tables: List[Dict[str, Any]]
    statistics: ExtractionStatistics
    metadata: ExtractionMetadata
    output_path: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "success": self.success,
            "tables": self.tables,
            "statistics": self.statistics.to_dict(),
            "metadata": self.metadata.to_dict(),
        }
        if self.output_path is not None:
            response["output_path"] = self.output_path
        if self.error is not None:
            response["error"] = self.error
        return response
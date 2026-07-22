"""
Table Extractor Configuration

Centralizes all tunable constants for the table extraction pipeline so
that extractor.py consumes configuration rather than defining it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class ExtractorConfig:
    """Immutable configuration for TableExtractor."""

    supported_image_extensions: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
        )
    )
    supported_pdf_extensions: FrozenSet[str] = field(
        default_factory=lambda: frozenset({".pdf"})
    )
    supported_mime_types: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                "application/pdf",
                "image/png",
                "image/jpeg",
                "image/bmp",
                "image/tiff",
                "image/webp",
            }
        )
    )
    supported_output_formats: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {"json", "csv", "excel", "markdown", "html"}
        )
    )
    max_file_size_bytes: int = 200 * 1024 * 1024
    default_output_format: str = "json"
    pdf_dpi: int = 300
    response_version: str = "1.0"

    @property
    def supported_extensions(self) -> FrozenSet[str]:
        return self.supported_image_extensions | self.supported_pdf_extensions


DEFAULT_CONFIG = ExtractorConfig()
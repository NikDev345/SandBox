"""
Table Extractor

Pure orchestration layer for the table extraction pipeline. Coordinates
file validation, document loading, page iteration, service calls, result
collection, statistics, and response construction.

This module holds no knowledge of PaddleOCR, prediction formats, OCR
field names, table field names, HTML, bounding boxes, cells, or structure
dictionaries. All of that belongs to PaddleTableClient and parser.py.
Formatting decisions belong to TableFormatter.
"""

from __future__ import annotations

import logging
import mimetypes
import time
from pathlib import Path
from typing import List, Optional

from PIL import Image

from app.services.table_extractor.config import DEFAULT_CONFIG, ExtractorConfig
from app.services.table_extractor.formatter import TableFormatter
from app.models.table_extractor import (
    ExtractionMetadata,
    ExtractionResponse,
    ExtractionStatistics,
    OcrResult,
    PageResult,
)
from app.services.table_extractor.paddle_client import PaddleTableClient
from app.services.table_extractor.parser import TableParser
from app.services.table_extractor.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------


class TableExtractorError(Exception):
    """Base exception for table extraction failures."""


class FileValidationError(TableExtractorError):
    """Raised when an input file fails validation."""


class UnsupportedFileTypeError(TableExtractorError):
    """Raised when a file type is not supported."""


class DocumentLoadError(TableExtractorError):
    """Raised when a document cannot be loaded or converted to pages."""


# ------------------------------------------------------------------------------
# Extractor
# ------------------------------------------------------------------------------


class TableExtractor:
    """
    Orchestrates the table extraction pipeline.

    This class coordinates services only: it validates input, loads
    pages, asks PaddleTableClient for table and OCR predictions, asks
    TableParser to parse them, asks TableFormatter to format the result,
    and assembles the final response. It performs no OCR, no table
    structure recognition, no HTML parsing, no table reconstruction, and
    no output formatting itself.
    """

    def __init__(
        self,
        table_client: Optional[PaddleTableClient] = None,
        pdf_processor: Optional[PDFProcessor] = None,
        parser: Optional[TableParser] = None,
        formatter: Optional[TableFormatter] = None,
        config: ExtractorConfig = DEFAULT_CONFIG,
    ) -> None:
        self._config = config
        self._table_client = table_client or PaddleTableClient()
        self._pdf_processor = pdf_processor or PDFProcessor(dpi=config.pdf_dpi)
        self._parser = parser or TableParser()
        self._formatter = formatter or TableFormatter()

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def extract(
        self,
        file_path: str,
        output_format: str = "",
        fast_mode: bool = False,
    ) -> dict:
        """
        Run the full extraction pipeline on a single file and return a
        structured response dictionary. Never raises — all failures are
        captured and returned as structured error information.
        """
        start_time = time.monotonic()
        output_format = (output_format or self._config.default_output_format).lower()

        try:
            self._validate_file(file_path)
            file_type = self._detect_file_type(file_path)
            pages = self._load_pages(file_path, file_type)

            if not pages:
                logger.warning("No pages could be loaded from %s", file_path)
                return self._create_response(
                    success=True,
                    tables=[],
                    statistics=self._collect_statistics(
                        page_count=0, table_count=0, ocr_item_count=0,
                        processing_time=time.monotonic() - start_time,
                    ),
                    output_format=output_format,
                ).to_dict()

            logger.info("Loaded %d page(s) from %s", len(pages), file_path)

            all_parsed_tables: List[dict] = []
            total_ocr_items = 0

            for page_number, image in enumerate(pages, start=1):
                page_start = time.monotonic()
                try:
                    page_result = self._process_page(image, page_number, fast_mode)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to process page %d of %s: %s",
                        page_number, file_path, exc, exc_info=True,
                    )
                    continue

                parsed_tables = self._parse_tables(page_result)
                all_parsed_tables.extend(parsed_tables)
                total_ocr_items += page_result.ocr_result.item_count

                logger.info(
                    "Processed page %d/%d in %.3fs (%d table(s) found)",
                    page_number, len(pages), time.monotonic() - page_start,
                    len(parsed_tables),
                )

            if not all_parsed_tables:
                logger.warning("No tables detected in %s", file_path)

            output_path = self._format_output(all_parsed_tables, output_format)

            statistics = self._collect_statistics(
                page_count=len(pages),
                table_count=len(all_parsed_tables),
                ocr_item_count=total_ocr_items,
                processing_time=time.monotonic() - start_time,
            )

            return self._create_response(
                success=True,
                tables=all_parsed_tables,
                statistics=statistics,
                output_format=output_format,
                output_path=output_path,
            ).to_dict()

        except TableExtractorError as exc:
            logger.error("Extraction failed for %s: %s", file_path, exc)
            return self._create_error_response(str(exc), output_format, start_time).to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error extracting %s", file_path)
            return self._create_error_response(
                f"Unexpected error: {exc}", output_format, start_time
            ).to_dict()

    # --------------------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------------------

    def _validate_file(self, file_path: str) -> None:
        """Validate existence, readability, extension, size, and MIME type."""
        if not file_path:
            raise FileValidationError("No file path provided.")

        path = Path(file_path)

        if not path.exists():
            raise FileValidationError(f"File does not exist: {file_path}")

        if not path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")

        try:
            with open(path, "rb") as handle:
                handle.read(1)
        except OSError as exc:
            raise FileValidationError(f"File is not readable: {file_path} ({exc})") from exc

        extension = path.suffix.lower()
        if extension not in self._config.supported_extensions:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{extension}'. "
                f"Supported: {sorted(self._config.supported_extensions)}"
            )

        size = path.stat().st_size
        if size <= 0:
            raise FileValidationError(f"File is empty: {file_path}")
        if size > self._config.max_file_size_bytes:
            raise FileValidationError(
                f"File exceeds maximum allowed size of "
                f"{self._config.max_file_size_bytes // (1024 * 1024)}MB: {file_path}"
            )

        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is not None and mime_type not in self._config.supported_mime_types:
            raise UnsupportedFileTypeError(
                f"Unsupported MIME type '{mime_type}' for file: {file_path}"
            )

        logger.info("File validated: %s (%.2f KB)", file_path, size / 1024)

    # --------------------------------------------------------------------------
    # File Type Detection
    # --------------------------------------------------------------------------

    def _detect_file_type(self, file_path: str) -> str:
        """Determine whether the file is a PDF or an image."""
        extension = Path(file_path).suffix.lower()

        if extension in self._config.supported_pdf_extensions:
            return "pdf"
        if extension in self._config.supported_image_extensions:
            return "image"

        raise UnsupportedFileTypeError(f"Cannot determine document type for: {file_path}")

    # --------------------------------------------------------------------------
    # Page Loading
    # --------------------------------------------------------------------------

    def _load_pages(self, file_path: str, file_type: str) -> List[Image.Image]:
        """Load pages as PIL images, delegating PDF conversion entirely."""
        if file_type == "pdf":
            try:
                pages = self._pdf_processor.convert_pdf(file_path)
            except FileNotFoundError as exc:
                raise DocumentLoadError(str(exc)) from exc
            except Exception as exc:  # noqa: BLE001
                raise DocumentLoadError(
                    f"Failed to convert PDF to images: {exc}"
                ) from exc

            if not pages:
                logger.warning("PDF %s contains no pages.", file_path)
                return []

            return pages

        if file_type == "image":
            try:
                image = Image.open(file_path)
                image.load()
            except Exception as exc:  # noqa: BLE001
                raise DocumentLoadError(
                    f"Failed to load image, file may be corrupted: {exc}"
                ) from exc

            return [image]

        raise UnsupportedFileTypeError(f"Unknown file type: {file_type}")

    # --------------------------------------------------------------------------
    # Page Processing
    # --------------------------------------------------------------------------

    def _process_page(
        self, image: Image.Image, page_number: int, fast_mode: bool = False
    ) -> PageResult:
        """
        Run table detection and OCR on a single page via PaddleTableClient.

        The extractor never touches model objects or raw prediction
        formats directly; PaddleTableClient returns already-normalized
        results. No parsing occurs here.
        """
        table_predictions = self._run_table_detection(image, page_number)
        ocr_result = self._run_ocr(image, page_number, fast_mode)

        return PageResult(
            page_number=page_number,
            image=image,
            table_predictions=table_predictions,
            ocr_result=ocr_result,
        )

    def _run_table_detection(self, image: Image.Image, page_number: int) -> List[dict]:
        """Request normalized table structure predictions from the service."""
        try:
            predictions = self._table_client.run_table_detection(image)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Table detection failed on page %d: %s",
                page_number, exc, exc_info=True,
            )
            return []

        logger.debug(
            "Table detection found %d candidate table(s) on page %d",
            len(predictions), page_number,
        )
        return predictions

    def _run_ocr(
        self, image: Image.Image, page_number: int, fast_mode: bool = False
    ) -> OcrResult:
        """Request normalized OCR results from the service."""
        try:
            ocr_result = self._table_client.run_ocr(image, skip_preprocessing=fast_mode)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "OCR failed on page %d: %s", page_number, exc, exc_info=True
            )
            return OcrResult()

        logger.debug(
            "OCR completed on page %d with %d recognized item(s)",
            page_number, ocr_result.item_count,
        )
        return ocr_result

    # --------------------------------------------------------------------------
    # Parsing
    # --------------------------------------------------------------------------

    def _parse_tables(self, page_result: PageResult) -> List[dict]:
        """Pass predictions to the parser for each detected table on a page."""
        page_number = page_result.page_number
        table_predictions = page_result.table_predictions
        ocr_data = page_result.ocr_result.data

        if not table_predictions:
            logger.debug("No table structure predictions on page %d, skipping parse.", page_number)
            return []

        if not ocr_data:
            logger.warning("No OCR predictions available for page %d.", page_number)
            return []

        parsed_tables: List[dict] = []

        for table_index, table_result in enumerate(table_predictions, start=1):
            try:
                parsed = self._parser.parse(
                    ocr_data,
                    table_result,
                    page_number,
                    table_index,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Parser failed on page %d, table %d: %s",
                    page_number, table_index, exc, exc_info=True,
                )
                continue

            if parsed:
                parsed_tables.extend(parsed)

        return parsed_tables

    # --------------------------------------------------------------------------
    # Formatting
    # --------------------------------------------------------------------------

    def _format_output(self, tables: List[dict], output_format: str) -> Optional[str]:
        """Request formatting from TableFormatter; exporting is its concern."""
        if output_format not in self._config.supported_output_formats:
            logger.warning(
                "Unsupported output format '%s', falling back to '%s'.",
                output_format, self._config.default_output_format,
            )
            output_format = self._config.default_output_format

        if not tables:
            logger.info("Skipping formatting step: no tables to format.")
            return None

        try:
            filename = f"extraction_{int(time.time())}"
            return self._formatter.export(tables, filename, output_format)
        except Exception as exc:  # noqa: BLE001
            logger.error("Formatting failed: %s", exc, exc_info=True)
            return None

    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------

    def _collect_statistics(
        self,
        page_count: int,
        table_count: int,
        ocr_item_count: int,
        processing_time: float,
    ) -> ExtractionStatistics:
        """Aggregate processing statistics for the response."""
        statistics = ExtractionStatistics(
            pages=page_count,
            tables=table_count,
            processing_time=round(processing_time, 3),
            ocr_items=ocr_item_count,
        )
        logger.info("Processing statistics: %s", statistics.to_dict())
        return statistics

    # --------------------------------------------------------------------------
    # Response Construction
    # --------------------------------------------------------------------------

    def _create_response(
        self,
        success: bool,
        tables: List[dict],
        statistics: ExtractionStatistics,
        output_format: str,
        output_path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ExtractionResponse:
        """Assemble the final structured response model."""
        metadata = ExtractionMetadata(
            format=output_format,
            version=self._config.response_version,
        )
        return ExtractionResponse(
            success=success,
            tables=tables,
            statistics=statistics,
            metadata=metadata,
            output_path=output_path,
            error=error,
        )

    def _create_error_response(
        self, error_message: str, output_format: str, start_time: float
    ) -> ExtractionResponse:
        """Build a structured error response without raising."""
        statistics = self._collect_statistics(
            page_count=0,
            table_count=0,
            ocr_item_count=0,
            processing_time=time.monotonic() - start_time,
        )
        return self._create_response(
            success=False,
            tables=[],
            statistics=statistics,
            output_format=output_format,
            error=error_message,
        )
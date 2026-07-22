"""
Table Extractor API

HTTP interface layer for the table extraction service. This module is
responsible only for receiving requests, authenticating callers,
validating uploads, persisting temporary files, invoking TableExtractor,
returning its response verbatim, and cleaning up. All OCR, parsing,
formatting, and extraction logic lives in
app.services.table_extractor.extractor.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.utils.auth import get_current_user
from app.models.user import Users
from app.services.table_extractor.extractor import (
    DocumentLoadError,
    FileValidationError,
    TableExtractor,
    TableExtractorError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/table-extractor", tags=["Table Extractor"])


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
}
SUPPORTED_OUTPUT_FORMATS = {"json", "csv", "excel", "markdown", "html"}
DEFAULT_OUTPUT_FORMAT = "json"

MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB

TEMP_UPLOAD_DIR = Path("/tmp/table_extractor_uploads")


# ------------------------------------------------------------------------------
# Dependency Provider
# ------------------------------------------------------------------------------


def get_table_extractor() -> TableExtractor:
    """Provide a TableExtractor instance for request handling."""
    return TableExtractor()


# ------------------------------------------------------------------------------
# Router
# ------------------------------------------------------------------------------


@router.post(
    "/extract",
    summary="Extract tables from an uploaded document",
    description=(
        "Uploads a PDF or image file and extracts all detected tables "
        "using OCR and table structure recognition. Supports PDF, PNG, "
        "JPG, JPEG, BMP, TIFF, and WEBP files up to 200MB. Output can be "
        "requested as json, csv, excel, markdown, or html."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Tables extracted successfully."},
        400: {"description": "The request or uploaded file failed validation."},
        401: {"description": "Authentication credentials were missing or invalid."},
        403: {"description": "The authenticated user is not permitted to perform this action."},
        413: {"description": "The uploaded file exceeds the maximum allowed size."},
        415: {"description": "The uploaded file type is not supported."},
        422: {"description": "The request could not be processed as specified."},
        500: {"description": "An unexpected server error occurred during extraction."},
    },
)
async def extract_tables(
    file: UploadFile = File(..., description="The PDF or image file to extract tables from."),
    output_format: Optional[str] = Form(
        default=DEFAULT_OUTPUT_FORMAT,
        description="Desired output format: json, csv, excel, markdown, or html.",
    ),
    fast_mode: bool = Form(
        default=False,
        description=(
            "Set true for clean digital documents (screenshots, PDF exports). "
            "Skips document-orientation, unwarping, and textline-orientation "
            "preprocessing for a significant speedup. Leave false for "
            "scanned/photographed documents that may be skewed or tilted."
        ),
    ),
    current_user: Users = Depends(get_current_user),
    extractor: TableExtractor = Depends(get_table_extractor),
) -> dict:
    """Validate the upload, run table extraction, and return the result."""
    request_start = time.monotonic()

    logger.info(
        "Table extraction request received from user_id=%s filename=%s",
        getattr(current_user, "id", "unknown"),
        file.filename,
    )

    normalized_format = _validate_output_format(output_format)
    _validate_upload_metadata(file)

    temp_file_path: Optional[Path] = None

    try:
        temp_file_path = await _save_upload_to_temp(file)

        logger.info(
            "Saved upload for user_id=%s as temp_file=%s size=%d bytes",
            getattr(current_user, "id", "unknown"),
            temp_file_path.name,
            temp_file_path.stat().st_size,
        )

        logger.info(
            "Starting extraction for user_id=%s temp_file=%s format=%s",
            getattr(current_user, "id", "unknown"),
            temp_file_path.name,
            normalized_format,
        )

        result = extractor.extract(str(temp_file_path), normalized_format, fast_mode)

        elapsed = time.monotonic() - request_start
        logger.info(
            "Extraction finished for user_id=%s temp_file=%s success=%s "
            "elapsed=%.3fs",
            getattr(current_user, "id", "unknown"),
            temp_file_path.name,
            result.get("success") if isinstance(result, dict) else None,
            elapsed,
        )

        if isinstance(result, dict) and not result.get("success", False):
            logger.warning(
                "Extraction reported failure for user_id=%s temp_file=%s error=%s",
                getattr(current_user, "id", "unknown"),
                temp_file_path.name,
                result.get("error"),
            )

        return result

    except FileValidationError as exc:
        logger.warning("File validation failed during extraction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except UnsupportedFileTypeError as exc:
        logger.warning("Unsupported file type during extraction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except DocumentLoadError as exc:
        logger.error("Document load failure during extraction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except TableExtractorError as exc:
        logger.error("Extractor error during extraction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Unexpected error during table extraction for user_id=%s filename=%s",
            getattr(current_user, "id", "unknown"),
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file.",
        ) from exc
    finally:
        _cleanup_temp_file(temp_file_path)


# ------------------------------------------------------------------------------
# Validation Helpers
# ------------------------------------------------------------------------------


def _validate_output_format(output_format: Optional[str]) -> str:
    """Validate and normalize the requested output format."""
    normalized = (output_format or DEFAULT_OUTPUT_FORMAT).strip().lower()
    if normalized not in SUPPORTED_OUTPUT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported output_format '{output_format}'. "
                f"Supported values: {sorted(SUPPORTED_OUTPUT_FORMATS)}"
            ),
        )
    return normalized


def _validate_upload_metadata(file: UploadFile) -> None:
    """Validate presence, filename, extension, and declared MIME type."""
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file was uploaded."
        )

    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file has no filename."
        )

    safe_name = _sanitize_filename(file.filename)
    extension = Path(safe_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file extension '{extension}'. "
                f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}"
            ),
        )

    if file.content_type is not None and file.content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type '{file.content_type}'.",
        )


def _sanitize_filename(filename: str) -> str:
    """Strip directory components to prevent path traversal."""
    candidate = Path(filename).name
    if not candidate or candidate in (".", ".."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename."
        )
    return candidate


# ------------------------------------------------------------------------------
# Temp File Handling
# ------------------------------------------------------------------------------


async def _save_upload_to_temp(file: UploadFile) -> Path:
    """
    Stream the upload to a randomly named temp file, enforcing the
    maximum size limit while writing so oversized files are rejected
    without buffering the entire payload in memory.
    """
    TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_filename(file.filename or "")
    extension = Path(safe_name).suffix.lower()
    temp_filename = f"{uuid.uuid4().hex}{extension}"
    temp_path = TEMP_UPLOAD_DIR / temp_filename

    if temp_path.exists():
        temp_filename = f"{uuid.uuid4().hex}{extension}"
        temp_path = TEMP_UPLOAD_DIR / temp_filename

    total_bytes = 0

    try:
        with open(temp_path, "wb") as destination:
            while True:
                chunk = await file.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    destination.close()
                    _delete_file_quietly(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"File exceeds maximum allowed size of "
                            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                        ),
                    )

                destination.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        _delete_file_quietly(temp_path)
        logger.error("Failed to write temporary upload file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file.",
        ) from exc
    finally:
        await file.close()

    if total_bytes == 0:
        _delete_file_quietly(temp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    return temp_path


def _cleanup_temp_file(temp_file_path: Optional[Path]) -> None:
    """Delete the temporary upload file, logging but not raising on failure."""
    if temp_file_path is None:
        return

    try:
        if temp_file_path.exists():
            temp_file_path.unlink()
            logger.info("Cleaned up temporary file: %s", temp_file_path.name)
    except OSError as exc:
        logger.error(
            "Failed to clean up temporary file %s: %s", temp_file_path.name, exc
        )


def _delete_file_quietly(path: Path) -> None:
    """Best-effort delete used during error paths, never raises."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        logger.warning("Could not remove partially written temp file: %s", path.name)
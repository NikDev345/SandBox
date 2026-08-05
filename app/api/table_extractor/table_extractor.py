"""
Table Extractor API

HTTP interface layer for the table extraction service. This module is
responsible only for receiving requests, authenticating callers,
validating uploads, persisting temporary files, invoking TableExtractor,
returning its response verbatim, and cleaning up. All OCR, parsing,
formatting, and extraction logic lives in
app.services.table_extractor.extractor.

IMPORTANT — process pool, not thread pool
-------------------------------------------
TableExtractor's pipeline is CPU-bound and can take tens of seconds
(PDF->image conversion, layout detection, table structure recognition,
OCR). It must not run directly on the asyncio event loop, and — for
this specific workload — a plain `run_in_threadpool` is not sufficient
either.

The reason: PaddleOCR/PaddlePaddle's C++ inference calls do not
reliably release Python's GIL for their full duration. A blocking
Python-level call moved to a worker *thread* still shares the same GIL
as the event loop thread; if a `predict()` call holds the GIL
continuously for seconds at a time, nothing else in the process can
execute Python bytecode meanwhile — including the event loop itself and
any WebSocket ping/pong traffic riding on it (e.g. NiceGUI's client
heartbeat). The visible symptom was the whole page silently reloading
partway through a long extraction, even after moving the call to
`run_in_threadpool`.

A separate OS process has its own independent GIL, so this problem
cannot happen across a process boundary. Extraction now runs in a
ProcessPoolExecutor via `run_extraction_pipeline`
(app.services.table_extractor.extractor), a module-level function with
no DB dependency — a SQLAlchemy Session cannot be pickled across
process boundaries. The DB execution-logging step happens back here in
the router, in the request's own process, right after the pooled call
returns.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.models.user import Users
from app.services.table_extractor.extractor import (
    DocumentLoadError,
    FileValidationError,
    TableExtractor,
    TableExtractorError,
    UnsupportedFileTypeError,
    run_extraction_pipeline,
)
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService


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

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB

TEMP_UPLOAD_DIR = Path("/tmp/table_extractor_uploads")

# Number of worker processes dedicated to table extraction. Each worker
# lazily loads its own copy of the PaddleOCR layout/structure/OCR models
# on first use and keeps them resident afterward (the pool is created
# once at import time and reused across requests, so this is a one-time
# cost per worker, not per request). Keep this modest — each loaded
# model set consumes meaningful CPU and RAM; size it to your available
# cores/memory rather than raising it to increase raw concurrency.
EXTRACTION_POOL_WORKERS = 2

# Created once at module import time and reused for the lifetime of the
# server process. Do NOT create a new ProcessPoolExecutor per request —
# that would reload the PaddleOCR models from scratch every single time.
_extraction_pool = ProcessPoolExecutor(max_workers=EXTRACTION_POOL_WORKERS)


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
        "JPG, JPEG, BMP, TIFF, and WEBP files up to 20MB. Output can be "
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
    db: Session = Depends(get_db),
) -> dict:
    """Validate the upload, run table extraction, and return the result."""
    request_start = time.monotonic()


    normalized_format = _validate_output_format(output_format)
    _validate_upload_metadata(file)

    temp_file_path: Optional[Path] = None

    try:
        temp_file_path = await _save_upload_to_temp(file)

        # ------------------------------------------------------------
        # Run the CPU-bound extraction pipeline in a separate process,
        # not a thread. See the module docstring above for why a thread
        # (even via run_in_threadpool) is not sufficient for this
        # specific workload. `run_extraction_pipeline` is a
        # module-level, DB-free function — the only thing that can
        # cross a process boundary here is plain, picklable data
        # (file path, strings, bools) in and a plain dict out.
        # ------------------------------------------------------------
        loop = asyncio.get_running_loop()
        response, file_type = await loop.run_in_executor(
            _extraction_pool,
            run_extraction_pipeline,
            str(temp_file_path),
            normalized_format,
            fast_mode,
        )

        # DB logging happens here, back in the request's own process,
        # using the `db` session FastAPI already gave us for this
        # request — never inside the pooled worker.
        _log_execution(
            db=db,
            user_id=current_user['sub'],
            file_path=temp_file_path,
            file_type=file_type,
            output_format=normalized_format,
            fast_mode=fast_mode,
            response=response,
        )

        elapsed = time.monotonic() - request_start

        if isinstance(response, dict) and not response.get("success", False):
            print(
                "Extraction reported failure for user_id=%s temp_file=%s error=%s",
                getattr(current_user, "id", "unknown"),
                temp_file_path.name,
                response.get("error"),
            )

        return response

    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except DocumentLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except TableExtractorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        print(
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
# Execution Logging
# ------------------------------------------------------------------------------


def _log_execution(
    db: Session,
    user_id: str,
    file_path: Path,
    file_type: Optional[str],
    output_format: str,
    fast_mode: bool,
    response: dict,
) -> None:
    """
    Record an execution log entry for this extraction run. Must run in
    the request's own process (the one holding `db`) — never inside the
    ProcessPoolExecutor worker, since a SQLAlchemy Session cannot be
    pickled across a process boundary. Never raises; logging failures
    should not fail the user-facing request.
    """
    validated_input = {
        "filename": file_path.name,
        "file_type": file_type,
        "output_format": output_format,
        "fast_mode": fast_mode,
    }

    try:
        tool = ToolService.get_tool_by_slug(db=db, slug="TABLE-EXTRACTOR")
        tool_id = tool.id if tool else "TABLE-EXTRACTOR"

        ExecutionService.create_execution(
            db=db,
            user_id=user_id,
            tool_id=tool_id,
            user_input=json.dumps(validated_input),
            output=json.dumps(response),
        )
    except Exception:
        pass

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
    except OSError as exc:
        raise OSError(
            "Failed to clean up temporary file %s: %s", temp_file_path.name, exc
        )


def _delete_file_quietly(path: Path) -> None:
    """Best-effort delete used during error paths, never raises."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        raise OSError("Could not remove partially written temp file: %s", path.name)
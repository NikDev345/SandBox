"""
app/services/image_text_extractor.py

Singleton service that orchestrates image-to-text extraction.

Responsibilities
----------------
- Validate uploaded files (presence, MIME type, extension, size)
- Decode and preprocess images
- Delegate OCR to the shared ocr_client
- Compute statistics and generate quality warnings
- Return structured ImageTextExtractorResponse

The service never imports RapidOCR directly; all OCR communication
goes through app.services.ocr.factory.ocr_client.
"""

import logging
import threading
import time
from typing import Optional

import numpy as np
from fastapi import UploadFile

from app.models.image_text_extractor import (
    ImageTextExtractorRequest,
    ImageTextExtractorResponse,
    OCRResult,
    OCRStatistics,
)
from app.services.ocr.factory import ocr_client
from app.utils.image_processing import (
    load_image,
    preprocess_for_ocr,
    validate_extension,
    validate_size,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/bmp",
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/tiff",
        "image/webp",
    }
)

_CONFIDENCE_WARNING_THRESHOLD: float = 75.0
_SMALL_IMAGE_PIXELS: int = 100 * 100
_LARGE_IMAGE_PIXELS: int = 4000 * 4000
_SUSPICIOUS_ASPECT_RATIO: float = 2.5


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ImageTextExtractorService:
    """Singleton service that orchestrates image text extraction via OCR.

    All OCR communication is delegated to ``ocr_client``; this service
    contains no OCR implementation details.

    Usage::

        result = await image_text_extractor_service.process(file, request)
    """

    _instance: Optional["ImageTextExtractorService"] = None
    _instance_lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    # ------------------------------------------------------------------
    # Singleton lifecycle
    # ------------------------------------------------------------------

    def __new__(cls) -> "ImageTextExtractorService":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        with self._instance_lock:
            if self._initialized:
                return
            self._initialized = True
            logger.info("ImageTextExtractorService initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process(
        self,
        file: UploadFile,
        request: ImageTextExtractorRequest,
    ) -> ImageTextExtractorResponse:
        """Run the full OCR workflow for a single uploaded image.

        Args:
            file: Incoming multipart upload from FastAPI.
            request: Extraction configuration (language, enhance_image, …).

        Returns:
            ``ImageTextExtractorResponse`` containing the OCR result and
            computed statistics.

        Raises:
            ValueError: On any validation failure (MIME type, extension,
                size, empty file, undecodable image).
            RuntimeError: If OCR extraction fails for any reason.
        """
        filename: str = file.filename or "unknown"
        logger.info("OCR started | file=%s", filename)
        start_time: float = time.perf_counter()

        try:
            self._validate_upload(file)
            self._validate_content_type(file)
            self._validate_extension(filename)

            raw_bytes: bytes = await self._read_upload(file)
            self._validate_size(raw_bytes)

            image: np.ndarray = self._load_image(raw_bytes, filename)
            preprocessed: np.ndarray = self._preprocess_image(image, filename)

            ocr_raw = await self._extract(preprocessed)

            elapsed: float = time.perf_counter() - start_time
            statistics: OCRStatistics = self._calculate_statistics(
                ocr_raw, preprocessed, elapsed
            )
            warnings: list[str] = self._generate_warnings(
                ocr_raw, preprocessed, statistics
            )
            result: OCRResult = self._build_result(ocr_raw, statistics, warnings, filename,request)
            response: ImageTextExtractorResponse = self._build_response(result, request)

            logger.info(
                "OCR completed | file=%s | chars=%d | confidence=%.2f | elapsed=%.3fs",
                filename,
                statistics.characters,
                statistics.confidence,
                elapsed,
            )
            return response

        except ValueError as exc:
            logger.error("Validation failed | file=%s | error=%s", filename, exc)
            raise
        except RuntimeError as exc:
            logger.error("OCR runtime error | file=%s | error=%s", filename, exc)
            raise
        except Exception as exc:
            logger.exception(
                "Unexpected error during OCR | file=%s | error=%s", filename, exc
            )
            raise RuntimeError(
                f"OCR processing failed for '{filename}': {exc}"
            ) from exc
        finally:
            await self._cleanup(file)

    # ------------------------------------------------------------------
    # Private — validation
    # ------------------------------------------------------------------

    def _validate_upload(self, file: UploadFile) -> None:
        """Ensure the UploadFile object is present and carries a filename.

        Args:
            file: Incoming UploadFile.

        Raises:
            ValueError: If the file object is missing or has no filename.
        """
        if file is None:
            raise ValueError("No file was provided.")
        if not file.filename:
            raise ValueError("Uploaded file has no filename.")

    def _validate_content_type(self, file: UploadFile) -> None:
        """Reject files whose declared MIME type is not supported.

        Args:
            file: Incoming UploadFile.

        Raises:
            ValueError: If the MIME type is absent or unsupported.
        """
        content_type: Optional[str] = file.content_type
        if not content_type:
            raise ValueError("Uploaded file has no declared content type.")

        normalised: str = content_type.split(";")[0].strip().lower()
        if normalised not in _SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Unsupported MIME type '{normalised}'. "
                f"Supported types: {sorted(_SUPPORTED_MIME_TYPES)}"
            )

    def _validate_extension(self, filename: str) -> None:
        """Delegate extension validation to the shared image utility.

        Args:
            filename: Original filename string.

        Raises:
            ValueError: If the extension is not supported.
        """
        try:
            validate_extension(filename)
        except Exception as exc:
            raise ValueError(str(exc)) from exc

    def _validate_size(self, raw_bytes: bytes) -> None:
        """Delegate size validation to the shared image utility.

        Args:
            raw_bytes: Raw file bytes already read from the upload.

        Raises:
            ValueError: If the file exceeds the maximum allowed size.
        """
        try:
            validate_size(len(raw_bytes))
        except Exception as exc:
            raise ValueError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Private — I/O
    # ------------------------------------------------------------------

    async def _read_upload(self, file: UploadFile) -> bytes:
        """Read all bytes from the UploadFile without blocking the event loop.

        Args:
            file: Incoming UploadFile.

        Returns:
            Raw file bytes.

        Raises:
            ValueError: If the file is empty after reading.
            RuntimeError: If the read operation fails.
        """
        try:
            raw_bytes: bytes = await file.read()
        except Exception as exc:
            raise RuntimeError(f"Failed to read uploaded file: {exc}") from exc

        if not raw_bytes:
            raise ValueError("Uploaded file is empty.")

        return raw_bytes

    # ------------------------------------------------------------------
    # Private — image processing
    # ------------------------------------------------------------------

    def _load_image(self, raw_bytes: bytes, filename: str) -> np.ndarray:
        """Decode raw bytes into a NumPy image array.

        Args:
            raw_bytes: Raw file bytes.
            filename: Original filename (used in error messages).

        Returns:
            Decoded image as a NumPy ndarray.

        Raises:
            ValueError: If the bytes cannot be decoded into a valid image.
        """
        try:
            image: np.ndarray = load_image(raw_bytes)
        except Exception as exc:
            raise ValueError(f"Cannot decode image '{filename}': {exc}") from exc

        if image is None or image.size == 0:
            raise ValueError(f"Decoded image is empty for file '{filename}'.")

        return image

    def _preprocess_image(self, image: np.ndarray, filename: str) -> np.ndarray:
        """Apply OCR-optimised preprocessing via the shared image utility.

        Args:
            image: Decoded image ndarray.
            filename: Original filename (used in error messages).

        Returns:
            Preprocessed image ndarray.

        Raises:
            ValueError: If preprocessing fails.
        """
        try:
            preprocessed: np.ndarray = preprocess_for_ocr(image)
        except Exception as exc:
            raise ValueError(
                f"Image preprocessing failed for '{filename}': {exc}"
            ) from exc

        return preprocessed

    # ------------------------------------------------------------------
    # Private — OCR extraction
    # ------------------------------------------------------------------

    async def _extract(self, image: np.ndarray) -> object:
        """Delegate text extraction to the OCR client.

        Args:
            image: Preprocessed image ndarray.

        Returns:
            OCR result object exposing ``.text``, ``.confidence``,
            ``.blocks``, and ``.raw``.

        Raises:
            RuntimeError: If the OCR client raises any exception.
        """
        try:
            result = await ocr_client.extract(image)
        except Exception as exc:
            logger.error("OCR client error | error=%s", exc)
            raise RuntimeError(f"OCR extraction failed: {exc}") from exc

        return result

    # ------------------------------------------------------------------
    # Private — statistics
    # ------------------------------------------------------------------

    def _calculate_statistics(
        self,
        ocr_raw: object,
        image: np.ndarray,
        elapsed: float,
    ) -> OCRStatistics:
        """Compute text and quality statistics from the OCR result.

        Args:
            ocr_raw: Result object returned by ``ocr_client.extract()``.
            image: Preprocessed image ndarray (used for language detection).
            elapsed: Wall-clock processing time in seconds.

        Returns:
            Populated ``OCRStatistics`` instance.
        """
        text: str = ocr_raw.text or ""
        confidence: float = float(ocr_raw.confidence or 0.0)
        blocks: list = ocr_raw.blocks or []

        lines: list[str] = [ln for ln in text.splitlines() if ln.strip()]
        words: list[str] = text.split()
        paragraphs: list[str] = [p.strip() for p in text.split("\n\n") if p.strip()]

        detected_language: str = "unknown"
        if blocks:
            langs: list[str] = [
                b.get("language")
                for b in blocks
                if isinstance(b, dict) and b.get("language")
            ]
            if langs:
                detected_language = max(set(langs), key=langs.count)

        return OCRStatistics(
            characters=len(text),
            words=len(words),
            lines=len(lines),
            paragraphs=len(paragraphs),
            confidence=round(confidence, 4),
            processing_time=round(elapsed, 4),
        )

    # ------------------------------------------------------------------
    # Private — warnings
    # ------------------------------------------------------------------

    def _generate_warnings(
        self,
        ocr_raw: object,
        image: np.ndarray,
        statistics: OCRStatistics,
    ) -> list[str]:
        """Produce quality warnings based on heuristic thresholds.

        Args:
            ocr_raw: OCR result object.
            image: Preprocessed image ndarray.
            statistics: Computed OCR statistics.

        Returns:
            List of warning strings (may be empty).
        """
        warnings: list[str] = []
        text: str = ocr_raw.text or ""

        if not text.strip():
            warnings.append("No text was detected in the image.")

        if statistics.confidence < _CONFIDENCE_WARNING_THRESHOLD and text.strip():
            warnings.append(
                f"Low OCR confidence ({statistics.confidence:.0%}). "
                "Results may contain errors."
            )

        h: int
        w: int
        h, w = image.shape[:2]
        pixel_count: int = h * w

        if pixel_count < _SMALL_IMAGE_PIXELS:
            warnings.append(
                f"Image is very small ({w}×{h} px). OCR accuracy may be reduced."
            )

        if pixel_count > _LARGE_IMAGE_PIXELS:
            warnings.append(
                f"Image is very large ({w}×{h} px). Processing time may be elevated."
            )

        aspect_ratio: float = max(w, h) / max(min(w, h), 1)
        if aspect_ratio > _SUSPICIOUS_ASPECT_RATIO:
            warnings.append(
                "Unusual aspect ratio detected. "
                "The document may be rotated or incorrectly cropped."
            )

        if warnings:
            logger.warning(
                "OCR warnings | count=%d | warnings=%s", len(warnings), warnings
            )

        return warnings

    # ------------------------------------------------------------------
    # Private — builders
    # ------------------------------------------------------------------

    def _build_result(
        self,
        ocr_raw,
        statistics: OCRStatistics,
        warnings: list[str],
        filename: str,
        request: ImageTextExtractorRequest,
    ) -> OCRResult:

        """Assemble the ``OCRResult`` domain object.

        Args:
            ocr_raw: Raw OCR result object.
            statistics: Computed statistics.
            warnings: Generated warning messages.
            filename: Original filename for traceability.

        Returns:
            Populated ``OCRResult`` instance.
        """
        return OCRResult(
            filename=filename,
            language=request.language or "auto",
            extracted_text=ocr_raw.text or "",
            statistics=statistics,
            warnings=warnings,
        )

    def _build_response(
        self,
        result: OCRResult,
        request: ImageTextExtractorRequest,
    ) -> ImageTextExtractorResponse:
        """Wrap the ``OCRResult`` in the top-level API response envelope.

        Args:
            result: Completed OCR result.
            request: Original extraction request.

        Returns:
            ``ImageTextExtractorResponse`` ready for JSON serialisation.
        """
        return ImageTextExtractorResponse(
            success=True,
            message="OCR extraction completed successfully.",
            result=result,
        )

    # ------------------------------------------------------------------
    # Private — cleanup
    # ------------------------------------------------------------------

    async def _cleanup(self, file: UploadFile) -> None:
        """Release resources held by the UploadFile.

        Args:
            file: The UploadFile whose underlying stream should be closed.
        """
        try:
            await file.close()
        except Exception as exc:
            logger.warning("Failed to close UploadFile: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

image_text_extractor_service = ImageTextExtractorService()
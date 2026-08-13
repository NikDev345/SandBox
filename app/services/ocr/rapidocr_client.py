"""
app/services/ocr/rapidocr_client.py
-----------------------------------

RapidOCR client implementation for Sandbox AI SaaS.

Responsibilities
----------------
- Thread-safe singleton
- Lazy initialization of RapidOCR
- Initialize RapidOCR only when OCR is actually requested
- Execute OCR asynchronously
- Normalize RapidOCR output
- Return standardized OCRResult objects
"""

from __future__ import annotations

import asyncio
import threading

import numpy as np

from app.services.ocr.base import (
    BaseOCRClient,
    OCRBlock,
    OCRResult,
)


class RapidOCRClient(BaseOCRClient):

    _instance: "RapidOCRClient | None" = None
    _lock = threading.Lock()

    def __new__(cls):

        if cls._instance is None:

            with cls._lock:

                if cls._instance is None:
                    cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):

        if getattr(self, "_initialized", False):
            return

        # RapidOCR is intentionally NOT initialized here.
        #
        # This client is imported during application startup.
        # Initializing RapidOCR here would make every application
        # startup pay the OCR model initialization cost.
        self._ocr = None

        # Separate lock for lazy model initialization.
        self._ocr_lock = threading.Lock()

        self._initialized = True

    # ---------------------------------------------------------
    # Lazy RapidOCR Initialization
    # ---------------------------------------------------------

    def _get_ocr(self):
        """
        Lazily initialize RapidOCR.

        RapidOCR is created only when the Image Text Extractor
        actually receives an OCR request.

        This prevents OCR model initialization from slowing down
        application startup and Vercel cold starts.
        """

        if self._ocr is None:

            with self._ocr_lock:

                # Double-check after acquiring the lock.
                # Another thread may have initialized the model
                # while this thread was waiting.
                if self._ocr is None:

                    from rapidocr import RapidOCR

                    self._ocr = RapidOCR()

        return self._ocr

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    async def extract(
        self,
        image: np.ndarray,
    ) -> OCRResult:

        return await asyncio.to_thread(
            self._extract_sync,
            image,
        )

    # ---------------------------------------------------------
    # Internal OCR
    # ---------------------------------------------------------

    def _extract_sync(
        self,
        image: np.ndarray,
    ) -> OCRResult:

        try:

            ocr = self._get_ocr()

            output = ocr(image)

            return self._normalize(output)

        except Exception as exc:

            raise RuntimeError(
                "RapidOCR extraction failed."
            ) from exc

    # ---------------------------------------------------------
    # Normalize Output
    # ---------------------------------------------------------

    def _normalize(self, output) -> OCRResult:

        if output is None:
            return OCRResult(
                text="",
                confidence=0.0,
                blocks=[],
                raw=None,
            )

        # Pair bbox + text + score, then sort
        # top-to-bottom, left-to-right.
        items = sorted(
            zip(
                output.boxes,
                output.txts,
                output.scores,
            ),
            key=lambda x: (
                round(
                    x[0][:, 1].min() / 20
                ) * 20,
                x[0][:, 0].min(),
            ),
        )

        blocks: list[OCRBlock] = []
        total_score = 0.0

        for bbox, text, score in items:

            blocks.append(
                OCRBlock(
                    text=text,
                    confidence=float(score * 100),
                    bbox=bbox.tolist(),
                )
            )

            total_score += score

        confidence = (
            (total_score / len(output.scores)) * 100
            if output.scores
            else 0.0
        )

        return OCRResult(
            text="\n".join(
                text
                for _, text, _ in items
            ),
            confidence=round(
                confidence,
                2,
            ),
            blocks=blocks,
            raw=output,
        )


# ---------------------------------------------------------
# Singleton Instance
# ---------------------------------------------------------

rapidocr_client = RapidOCRClient()
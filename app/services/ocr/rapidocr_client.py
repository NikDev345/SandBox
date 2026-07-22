"""
app/services/ocr/rapidocr_client.py
-----------------------------------

RapidOCR client implementation for Sandbox AI SaaS.

Responsibilities
----------------
- Thread-safe singleton
- Initialize RapidOCR once
- Execute OCR asynchronously
- Normalize RapidOCR output
- Return standardized OCRResult objects
"""

from __future__ import annotations

import asyncio
import logging
import threading

from nicegui.html import output
import numpy as np
from rapidocr import RapidOCR

from app.services.ocr.base import (
    BaseOCRClient,
    OCRBlock,
    OCRResult,
)

logger = logging.getLogger(__name__)


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

        logger.info("Initializing RapidOCR...")

        self._ocr = RapidOCR()

        self._initialized = True

        logger.info("RapidOCR initialized successfully.")

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

            output = self._ocr(image)
            return self._normalize(output)

        except Exception as exc:

            logger.exception(
                "RapidOCR execution failed."
            )

            raise RuntimeError(
                "RapidOCR extraction failed."
            ) from exc

    # ---------------------------------------------------------
    # Normalize Output
    # ---------------------------------------------------------

    def _normalize(self, output) -> OCRResult:
        if output is None:
            return OCRResult(text="", confidence=0.0, blocks=[], raw=None)

    # Pair bbox + text + score, then sort top-to-bottom, left-to-right
        items = sorted(
            zip(output.boxes, output.txts, output.scores),
            key=lambda x: (round(x[0][:, 1].min() / 20) * 20, x[0][:, 0].min())
        )

        blocks: list[OCRBlock] = []
        total_score = 0.0

        for bbox, text, score in items:
            blocks.append(OCRBlock(
                text=text,
                confidence=float(score * 100),
                bbox=bbox.tolist(),
            ))
            total_score += score

        confidence = (total_score / len(output.scores)) * 100 if output.scores else 0.0

        return OCRResult(
            text="\n".join(t for _, t, _ in items),
            confidence=round(confidence, 2),
            blocks=blocks,
            raw=output,
        )


rapidocr_client = RapidOCRClient()
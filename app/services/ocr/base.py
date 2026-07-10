"""
app/services/ocr/base.py
------------------------

Base interface for all OCR engines used in Sandbox.

Responsibilities
----------------
- Define a common OCR result model
- Define the OCR client interface
- Ensure every OCR engine returns the same structure
- Decouple ImageTextExtractorService from OCR implementations

Supported Engines
-----------------
- RapidOCR
- PaddleOCR
- EasyOCR
- Google Vision
- Azure Document Intelligence
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ==========================================================
# OCR Result
# ==========================================================

@dataclass(slots=True)
class OCRBlock:
    """
    Represents a single detected text block.
    """

    text: str
    confidence: float
    bbox: list[list[float]] = field(default_factory=list)


@dataclass(slots=True)
class OCRResult:
    """
    Standard OCR result returned by every OCR engine.
    """

    text: str
    confidence: float
    blocks: list[OCRBlock]
    raw: Any = None


# ==========================================================
# Base OCR Client
# ==========================================================

class BaseOCRClient(ABC):
    """
    Abstract base class for all OCR clients.

    Every OCR engine must implement this interface.

    Example
    -------
    >>> result = await client.extract(image)
    >>> print(result.text)
    """

    @abstractmethod
    async def extract(
        self,
        image: np.ndarray,
    ) -> OCRResult:
        """
        Perform OCR on an image.

        Parameters
        ----------
        image:
            OpenCV BGR image.

        Returns
        -------
        OCRResult
            Standard Sandbox OCR result.

        Raises
        ------
        RuntimeError
            If OCR execution fails.
        """
        raise NotImplementedError
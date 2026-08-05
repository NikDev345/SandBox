"""
app/services/ocr/factory.py
---------------------------

OCR Client Factory

Responsibilities
----------------
- Select the active OCR engine
- Provide a singleton OCR client
- Hide OCR implementation details from the service layer

Supported Engines
-----------------
- RapidOCR (default)
- PaddleOCR (future)
- EasyOCR (future)
"""

from __future__ import annotations

import os

from app.services.ocr.base import BaseOCRClient
from app.services.ocr.rapidocr_client import RapidOCRClient


# ==========================================================
# Configuration
# ==========================================================

OCR_ENGINE = os.getenv("OCR_ENGINE", "rapid").lower()

# ==========================================================
# Factory
# ==========================================================

def create_ocr_client() -> BaseOCRClient:
    """
    Create the configured OCR client.
    """

    if OCR_ENGINE == "rapid":
        return RapidOCRClient()

    raise ValueError(
        f"Unsupported OCR engine: {OCR_ENGINE}"
    )

# ==========================================================
# Singleton Instance
# ==========================================================

ocr_client: BaseOCRClient = create_ocr_client()
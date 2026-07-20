"""
Table Parser

Uses PaddleOCR Table Structure Recognition to extract structured tables
from images.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paddleocr import TableStructureRecognition


class TableParser:
    """
    Extracts structured tables from images using PaddleOCR.
    """

    def __init__(self) -> None:
        self.model = TableStructureRecognition(
            model_name="SLANet"
        )

    def parse(
        self,
        image_path: str | Path
    ) -> dict[str, Any]:
        """
        Extract tables from an image.

        Args:
            image_path: Image file path

        Returns:
            Dictionary containing extracted table data.
        """

        image_path = str(image_path)

        results = self.model.predict(image_path)

        tables = []

        for index, result in enumerate(results):

            table = {
                "table_index": index + 1,
                "structure": [],
                "cells": [],
                "html": "",
                "confidence": None,
            }

            # HTML representation
            if "html" in result:
                table["html"] = result["html"]

            # Structure tokens
            if "structure" in result:
                table["structure"] = result["structure"]

            # Cell information
            if "cells" in result:
                table["cells"] = result["cells"]

            # Confidence
            if "score" in result:
                table["confidence"] = result["score"]

            tables.append(table)

        return {
            "success": True,
            "tables_found": len(tables),
            "tables": tables,
        }

    def has_tables(
        self,
        image_path: str | Path
    ) -> bool:
        """
        Quick helper to determine whether
        any tables exist in the image.
        """

        result = self.parse(image_path)

        return result["tables_found"] > 0
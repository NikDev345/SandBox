"""
PDF Processor

Utility class for converting PDF documents into images that can be
processed by the Table Extractor.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from PIL import Image


class PDFProcessor:
    """
    Handles PDF processing utilities.
    """

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def convert_pdf(
        self,
        pdf_path: str | Path,
    ) -> List[Image.Image]:
        """
        Convert every page of a PDF into PIL Images.

        Args:
            pdf_path: Path to the PDF.

        Returns:
            List[PIL.Image.Image]
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        images = convert_from_path(
            str(pdf_path),
            dpi=self.dpi
        )

        return images

    def save_pages(
        self,
        images: List[Image.Image],
        output_dir: str | Path,
        prefix: str = "page",
        image_format: str = "PNG",
    ) -> List[Path]:
        """
        Save images to disk.

        Returns:
            List of saved image paths.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        saved_paths: List[Path] = []

        for index, image in enumerate(images, start=1):

            file_path = output_dir / f"{prefix}_{index}.{image_format.lower()}"

            image.save(file_path, format=image_format)

            saved_paths.append(file_path)

        return saved_paths

    def create_temp_directory(self) -> Path:
        """
        Create a temporary working directory.
        """

        return Path(tempfile.mkdtemp())

    def cleanup(
        self,
        directory: str | Path,
    ) -> None:
        """
        Remove temporary directory.
        """

        directory = Path(directory)

        if directory.exists():
            shutil.rmtree(
                directory,
                ignore_errors=True
            )

    def page_count(
        self,
        pdf_path: str | Path,
    ) -> int:
        """
        Return the number of pages in a PDF.
        """

        images = self.convert_pdf(pdf_path)

        return len(images)
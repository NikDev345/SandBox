from __future__ import annotations

import re
from typing import List


class TextCleaner:
    """
    Utility class for cleaning extracted text before sending it to AI.

    Responsibilities:
    - Normalize whitespace
    - Remove excessive blank lines
    - Remove page numbers
    - Remove repeated headers/footers
    - Trim long documents
    """

    MAX_CHARACTERS = 50000

    @classmethod
    def clean(cls, text: str) -> str:
        """
        Complete cleaning pipeline.
        """

        if not text:
            return ""

        text = cls.normalize_newlines(text)
        text = cls.remove_page_numbers(text)
        text = cls.remove_multiple_spaces(text)
        text = cls.remove_empty_lines(text)
        text = cls.remove_duplicate_lines(text)
        text = cls.trim(text)

        return text.strip()

    # --------------------------------------------------
    # Individual Cleaning Steps
    # --------------------------------------------------

    @staticmethod
    def normalize_newlines(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def remove_multiple_spaces(text: str) -> str:
        return re.sub(r"[ \t]+", " ", text)

    @staticmethod
    def remove_empty_lines(text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text)

    @staticmethod
    def remove_page_numbers(text: str) -> str:
        """
        Removes standalone page numbers.

        Example:
            1
            Page 4
            PAGE 10
        """

        patterns = [
            r"(?im)^page\s+\d+\s*$",
            r"(?im)^p\.\s*\d+\s*$",
            r"(?m)^\d+\s*$"
        ]

        for pattern in patterns:
            text = re.sub(pattern, "", text)

        return text

    @staticmethod
    def remove_duplicate_lines(text: str) -> str:
        """
        Removes repeated consecutive lines.
        Useful for duplicated PDF headers/footers.
        """

        lines = text.split("\n")

        cleaned: List[str] = []

        previous = None

        for line in lines:

            stripped = line.strip()

            if not stripped:
                continue

            if stripped == previous:
                continue

            cleaned.append(stripped)

            previous = stripped

        return "\n".join(cleaned)

    @classmethod
    def trim(cls, text: str) -> str:
        """
        Prevent extremely large prompts.
        """

        if len(text) <= cls.MAX_CHARACTERS:
            return text

        return text[: cls.MAX_CHARACTERS]
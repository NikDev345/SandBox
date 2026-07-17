"""
Flashcard Generator Service
---------------------------
Coordinates the complete Flashcard Generator workflow.
"""

import json
import random
import re
import unicodedata

from pydantic import ValidationError

from app.models.flashcard_generator import (
    FlashcardGeneratorRequest,
    FlashcardGeneratorResponse,
)
from app.services.flashcard_generator.formatter import (
    FlashcardGeneratorFormatter,
)
from app.services.flashcard_generator.prompt_engine import (
    PromptEngine,
)
from app.services.flashcard_generator.validator import (
    FlashcardGeneratorValidator,
)
from app.services.gemini_service import GeminiService


class FlashcardGeneratorService:
    """
    Orchestrates the Flashcard Generator workflow.
    """

    @staticmethod
    async def generate(
        request: FlashcardGeneratorRequest,
        user=None,
    ) -> FlashcardGeneratorResponse:
        """
        Generate flashcards.
        """

        FlashcardGeneratorValidator.validate_request(request)

        cleaned_request = FlashcardGeneratorService._preprocess(request)

        prompt = PromptEngine.build_prompt(
            cleaned_request
        )

        raw_response = FlashcardGeneratorService._generate_flashcards(
            prompt
        )

        parsed_response = FlashcardGeneratorService._parse_json(
            raw_response
        )

        response = FlashcardGeneratorFormatter.format(
            parsed_response,
            cleaned_request.settings,
        )

        if cleaned_request.settings.shuffle_cards:
            random.shuffle(response.result.flashcards)

        FlashcardGeneratorService._validate_response(
            response,
            cleaned_request,
        )

        return response

    @staticmethod
    def _preprocess(
        request: FlashcardGeneratorRequest,
    ) -> FlashcardGeneratorRequest:
        """
        Clean and normalize request content before prompt construction.
        """

        content = FlashcardGeneratorService._clean_text(
            request.content
        )

        return FlashcardGeneratorRequest(
            content=content,
            settings=request.settings,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize unicode, remove invisible characters, and normalize whitespace.
        """

        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)

        text = text.replace("```json", "").replace("```", "")

        text = "".join(
            ch
            for ch in text
            if ch == "\n"
            or ch == "\t"
            or unicodedata.category(ch)[0] != "C"
        )

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = [line.strip() for line in text.split("\n")]

        cleaned_lines = []
        previous_blank = False

        for line in lines:

            if line == "":
                if previous_blank:
                    continue
                previous_blank = True
            else:
                previous_blank = False

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    @staticmethod
    def _generate_flashcards(prompt: str) -> str:
        """
        Generate raw flashcard JSON text with Gemini.
        """

        try:
            gemini = GeminiService()
            response = gemini.generate(prompt)
        except Exception as exc:
            raise RuntimeError(
                "Flashcard generation failed."
            ) from exc

        if not response or not response.strip():
            raise RuntimeError("Gemini returned an empty response.")

        return response

    @staticmethod
    def _parse_json(response: str) -> dict:
        """
        Parse and validate raw JSON returned by Gemini.
        """

        text = response.strip()

        if text.startswith("```"):
            text = (
                text.replace("```json", "")
                .replace("```", "")
                .strip()
            )

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Gemini returned malformed AI output."
            )

        if "flashcards" not in data:
            raise RuntimeError(
                "Gemini response is missing flashcards."
            )

        if not isinstance(data["flashcards"], list):
            raise RuntimeError(
                "Gemini response flashcards must be a list."
            )

        return data

    @staticmethod
    def _validate_response(
        response: FlashcardGeneratorResponse,
        request: FlashcardGeneratorRequest,
    ) -> None:
        """
        Validate the final typed response.
        """

        try:
            FlashcardGeneratorValidator.validate_response(
                response,
                request,
            )
        except ValidationError as exc:
            raise RuntimeError(
                "AI response validation failed."
            ) from exc

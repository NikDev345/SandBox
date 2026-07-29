"""
Brainstorm Generator Formatter

Converts Gemini's raw response into a BrainstormResponse.
"""

import json
import re

from app.models.brainstorm_generator import BrainstormResponse


class BrainstormFormatter:
    """Formats and validates Gemini responses."""

    @staticmethod
    def format(raw_response: str) -> BrainstormResponse:
        """
        Parse Gemini response into BrainstormResponse.
        """

        if not raw_response:
            raise ValueError("Gemini returned an empty response.")

        cleaned = BrainstormFormatter._clean_json(raw_response)

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON returned by Gemini: {e}"
            ) from e

        BrainstormFormatter._validate_required_fields(data)

        return BrainstormResponse(**data)

    @staticmethod
    def _clean_json(text: str) -> str:
        """
        Remove markdown code fences and surrounding whitespace.
        """

        text = text.strip()

        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"```$",
            "",
            text,
        )

        return text.strip()

    @staticmethod
    def _validate_required_fields(data: dict) -> None:
        """
        Ensure Gemini returned the required response structure.
        """

        required_fields = [
            "success",
            "summary",
            "ideas",
            "best_idea",
            "implementation_tips",
            "common_mistakes",
            "final_recommendation",
        ]

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                f"Missing required fields: {', '.join(missing)}"
            )

        if not isinstance(data["ideas"], list):
            raise ValueError("'ideas' must be a list.")

        if len(data["ideas"]) == 0:
            raise ValueError("Gemini returned no ideas.")

        for index, idea in enumerate(data["ideas"], start=1):

            required_idea_fields = [
                "title",
                "description",
                "why_it_works",
                "difficulty",
                "innovation_score",
                "next_steps",
            ]

            missing_fields = [
                field
                for field in required_idea_fields
                if field not in idea
            ]

            if missing_fields:
                raise ValueError(
                    f"Idea {index} is missing fields: "
                    f"{', '.join(missing_fields)}"
                )

            if not isinstance(idea["next_steps"], list):
                raise ValueError(
                    f"Idea {index}: 'next_steps' must be a list."
                )

            if not isinstance(
                idea["innovation_score"],
                (int, float),
            ):
                raise ValueError(
                    f"Idea {index}: innovation_score must be numeric."
                )

            score = float(idea["innovation_score"])

            if score < 0 or score > 10:
                raise ValueError(
                    f"Idea {index}: innovation_score must be between 0 and 10."
                )

            if idea["difficulty"] not in (
                "Easy",
                "Medium",
                "Hard",
            ):
                raise ValueError(
                    f"Idea {index}: invalid difficulty."
                )
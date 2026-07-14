"""
ELI5 Formatter
--------------
Parses and cleans AI-generated JSON explanations into the response model.
"""

import json
import re

from app.models.eli5 import ELI5Response, ImportantConcept
from app.utils.eli5 import clean_text


class ELI5Formatter:
    """
    Formats raw Gemini output into ELI5Response.
    """

    @staticmethod
    def format(explanation: str) -> ELI5Response:
        """
        Parse the Gemini JSON response into ELI5Response.

        Args:
            explanation: Raw string returned by GeminiService.generate().

        Returns:
            ELI5Response
        """
        text = explanation.strip()

        # Strip markdown code fences Gemini sometimes adds despite instructions
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Graceful fallback: surface whatever text came back in explanation
            return ELI5Response(
                summary="",
                explanation=clean_text(explanation),
                analogy="",
                important_concepts=[],
            )

        concepts = [
            ImportantConcept(
                title=c.get("title", "").strip(),
                description=c.get("description", "").strip(),
            )
            for c in data.get("important_concepts", [])
            if isinstance(c, dict)
        ]

        return ELI5Response(
            summary=clean_text(data.get("summary", "")),
            explanation=clean_text(data.get("explanation", "")),
            analogy=clean_text(data.get("analogy", "")),
            important_concepts=concepts,
        )
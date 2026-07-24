"""
============================================================
Decision Maker Formatter

Formats and validates Gemini responses.

Author: Sandbox AI
============================================================
"""

import json

from app.models.decision_maker import (
    DecisionAnalysis,
    DecisionMakerResponse,
    DecisionRecommendation,
)


class DecisionMakerFormatter:
    """Convert Gemini output into DecisionMakerResponse."""


    @staticmethod
    def format(response: str) -> DecisionMakerResponse:
        """
        Convert raw Gemini response into a validated model.
        """

        cleaned = DecisionMakerFormatter._clean_json(response)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "The AI returned an invalid JSON response."
            ) from exc

        recommendation = data.get("recommendation", {})

        analyses = []

        for item in data.get("analysis", []):
            analyses.append(
                DecisionAnalysis(
                    option=item.get("option", "Unknown"),
                    pros=item.get("pros", []),
                    cons=item.get("cons", []),
                    risks=item.get("risks", []),
                    score=float(item.get("score", 0))
                )
            )

        return DecisionMakerResponse(
            success=True,

            summary=data.get(
                "summary",
                "No summary available."
            ),

            recommendation=DecisionRecommendation(
                selected_option=recommendation.get(
                    "selected_option",
                    "Unknown"
                ),
                confidence=int(
                    recommendation.get("confidence", 0)
                ),
                reasoning=recommendation.get(
                    "reasoning",
                    "No reasoning provided."
                )
            ),

            analysis=analyses,

            key_factors=data.get(
                "key_factors",
                []
            ),

            final_advice=data.get(
                "final_advice",
                ""
            ),

            disclaimer=data.get(
                "disclaimer",
                "AI recommendations should support—not replace—your judgment."
            )
        )

    # ==========================================================
    # PRIVATE
    # ==========================================================

    @staticmethod
    def _clean_json(text: str) -> str:
        """
        Remove markdown code fences if Gemini returns them.
        """

        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()
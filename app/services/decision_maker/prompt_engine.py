"""
============================================================
Decision Maker Prompt Engine

Builds the prompt for the AI Decision Maker tool.

Author: Sandbox AI
============================================================
"""

from app.models.decision_maker import DecisionMakerRequest


class PromptEngine:
    """Build prompts for the Decision Maker AI."""


    @staticmethod
    def build_prompt(request: DecisionMakerRequest) -> str:
        """
        Build a structured prompt for Gemini.
        """

        criteria = request.criteria

        priorities = (
            "\n".join(f"- {p}" for p in criteria.priorities)
            if criteria and criteria.priorities
            else "None"
        )

        constraints = (
            "\n".join(f"- {c}" for c in criteria.constraints)
            if criteria and criteria.constraints
            else "None"
        )

        budget = (
            criteria.budget
            if criteria and criteria.budget
            else "Not specified"
        )

        timeline = (
            criteria.timeline
            if criteria and criteria.timeline
            else "Not specified"
        )

        context = (
            criteria.additional_context
            if criteria and criteria.additional_context
            else "None"
        )

        options = "\n".join(
            [
                f"{index + 1}. {option.title}"
                + (
                    f" - {option.description}"
                    if option.description
                    else ""
                )
                for index, option in enumerate(request.options)
            ]
        )

        return f"""
You are an expert decision analyst.

Your job is NOT to simply choose an option.

Instead:

• Compare every option objectively.
• Explain your reasoning.
• Identify trade-offs.
• Consider risks.
• Consider long-term consequences.
• Avoid bias.
• Be logical and evidence-based.

----------------------------------------------------

Decision Type:
{request.decision_type.value}

Decision Question:
{request.question}

Options:
{options}

Budget:
{budget}

Timeline:
{timeline}

Priorities:
{priorities}

Constraints:
{constraints}

Additional Context:
{context}

----------------------------------------------------

Return ONLY valid JSON.

Do NOT wrap it inside markdown.

Use EXACTLY this schema:

{{
    "summary": "...",

    "recommendation": {{
        "selected_option": "...",
        "confidence": 0,
        "reasoning": "..."
    }},

    "analysis": [
        {{
            "option": "...",
            "pros": [],
            "cons": [],
            "risks": [],
            "score": 0
        }}
    ],

    "key_factors": [],

    "final_advice": "...",

    "disclaimer":
        "This recommendation is AI-generated and should support—not replace—your personal judgment."
}}
"""
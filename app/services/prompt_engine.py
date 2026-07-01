from typing import Dict


class PromptEngine:
    """
    Centralized Prompt Builder for AI Text Summarizer.

    Responsibilities:
    - Build prompts only.
    - No AI calls.
    - No database access.
    - No business logic.

    The prompt automatically adapts to the selected summary length
    while preserving factual accuracy.
    """

    SUMMARY_LENGTHS: Dict[str, str] = {
        "short": """
Create a highly concise summary.

Requirements:
- Target approximately 10-30 words when possible.
- Capture only the core idea.
- Use one short paragraph or 2-3 bullet points.
- Remove all supporting details and examples.
""",

        "medium": """
Create a balanced summary.

Requirements:
- Target approximately 50-100 words when appropriate.
- Include all major ideas.
- Keep important supporting information.
- Organize naturally into one or two paragraphs.
""",

        "detailed": """
Create a comprehensive summary.

Requirements:
- Target approximately 100-200 words when the source text contains enough information.
- Preserve all important concepts, facts, names, numbers, dates, technical terms and conclusions.
- Maintain the logical flow of the original document.
- Include important supporting details.
- If the source text is short, produce the most detailed summary possible WITHOUT inventing new information.
""",
    }

    @staticmethod
    def build_summary_prompt(
        text: str,
        length: str = "medium",
    ) -> str:
        """
        Build a prompt for the AI Text Summarizer.

        Args:
            text: User input.
            length: short | medium | detailed

        Returns:
            Prompt string.
        """

        length = length.lower().strip()

        if length not in PromptEngine.SUMMARY_LENGTHS:
            raise ValueError(
                "Invalid summary length. Choose 'short', 'medium', or 'detailed'."
            )

        instruction = PromptEngine.SUMMARY_LENGTHS[length]

        return f"""
You are an expert AI Text Summarizer.

Your goal is to generate an accurate, readable, and faithful summary while preserving the original meaning.

Selected Summary Length:
{length.upper()}

Length Instructions:
{instruction}

General Rules:
1. Never invent facts, names, dates, numbers, statistics, or conclusions.
2. Never include information that is not present in the source.
3. Preserve factual accuracy.
4. Remove repetition and unnecessary wording.
5. Keep the summary clear, professional, and grammatically correct.
6. Preserve important technical terminology whenever applicable.
7. If the source contains headings, keep a similar structure whenever useful.
8. If the source contains bullet points, preserve them when appropriate.
9. Adapt the summary length according to the amount of information available.
10. If the source text is very short, DO NOT artificially increase the summary length.
11. Return ONLY the summary.
12. Do NOT explain your reasoning.
13. Do NOT include introductory phrases such as "Here is the summary".

Source Text:
--------------------
{text}
--------------------
""".strip()
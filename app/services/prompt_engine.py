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
            instructions: str | None = None,
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
            instruction_block = ""

            if instructions and instructions.strip():
                instruction_block = f"""
    Additional User Instructions:
    {instructions.strip()}

    Follow these instructions while remaining faithful to the original document.
    Do not invent or add information.
    """

            return f"""
    You are an expert AI Text Summarizer.

    Your goal is to generate an accurate, readable, and faithful summary while preserving the original meaning.

    Selected Summary Length:
    {length.upper()}

    Length Instructions:
    {instruction}

    {instruction_block}

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
        
    @staticmethod
    def build_blog_outline_prompt(request) -> str:
        return f"""
    You are an expert SEO strategist, professional content writer, and blog editor.

    Your task is to create a comprehensive, well-structured blog outline based on the user's requirements.

    ========================
    BLOG DETAILS
    ========================

    Topic:
    {request.topic}

    Target Audience:
    {request.audience.value}

    Blog Goal:
    {request.goal.value}

    Writing Tone:
    {request.tone.value}

    Outline Depth:
    {request.depth.value}

    Number of Main Sections:
    {request.sections}

    Language:
    {request.language.value}

    ========================
    CONTENT PREFERENCES
    ========================

    Introduction:
    {"Yes" if request.include_introduction else "No"}

    Conclusion:
    {"Yes" if request.include_conclusion else "No"}

    FAQs:
    {"Yes" if request.include_faqs else "No"}

    Call To Action:
    {"Yes" if request.include_cta else "No"}

    Statistics:
    {"Yes" if request.include_statistics else "No"}

    Examples:
    {"Yes" if request.include_examples else "No"}

    Case Studies:
    {"Yes" if request.include_case_studies else "No"}

    Internal Linking Ideas:
    {"Yes" if request.include_internal_links else "No"}

    External Resources:
    {"Yes" if request.include_external_resources else "No"}

    Key Takeaways:
    {"Yes" if request.include_key_takeaways else "No"}

    ========================
    SEO
    ========================

    Primary Keyword:
    {request.primary_keyword or "None"}

    Secondary Keywords:
    {", ".join(request.secondary_keywords) if request.secondary_keywords else "None"}

    ========================
    YOUR TASK
    ========================

    Generate a professional blog outline.

    The response MUST contain the following sections in this exact order.

    # Recommended Blog Title

    Provide the best SEO-friendly title.

    # Alternative Titles

    Generate 5 additional engaging titles.

    # Blog Summary

    Write a short overview describing what the article will cover.

    # Search Intent

    State the user's search intent.

    Example:

    - Informational
    - Commercial
    - Transactional
    - Navigational

    # Estimated Word Count

    Recommend an ideal article length.

    # Estimated Reading Time

    Estimate reading time.

    # Blog Outline

    Create a logical hierarchy using:

    H1

    H2

    H3

    H4 (only where necessary)

    Every section should include a short explanation of what should be written.

    # Frequently Asked Questions

    Generate useful FAQs readers are likely to search.

    # Suggested Statistics

    Suggest where statistics or research would strengthen the article.

    # Image Suggestions

    Suggest images, diagrams, tables, screenshots, or infographics.

    # Internal Linking Ideas

    Suggest related articles that could be linked.

    # External References

    Recommend trusted authoritative sources.

    # Meta Description

    Generate an SEO meta description under 160 characters.

    # URL Slug

    Generate an SEO-friendly URL slug.

    # Keywords

    Provide:

    • Primary Keyword

    • Secondary Keywords

    • Long-tail Keywords

    • LSI Keywords

    # Key Takeaways

    Summarize the article into concise bullet points.

    # Call To Action

    Generate a compelling CTA suitable for the topic.

    ========================
    RULES
    ========================

    - Use proper Markdown formatting.

    - Use clear headings.

    - Avoid repeating information.

    - Make the outline logical and easy to follow.

    - Ensure the article flows naturally.

    - Optimize for SEO.

    - Keep the outline highly actionable.

    - Do not generate the complete blog.

    - Only generate the outline and planning content.

    - Produce professional-quality output suitable for publication.

    Return only the final outline.
    """
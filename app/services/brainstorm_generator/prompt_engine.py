"""
Brainstorm Generator Prompt Engine

Responsible for building the prompt sent to Gemini.
"""

from app.models.brainstorm_generator import BrainstormRequest


class BrainstormPromptEngine:
    """Build prompts for the Brainstorm Generator."""

    @staticmethod
    def build_prompt(request: BrainstormRequest) -> str:
        """
        Build the complete Gemini prompt.
        """

        criteria = request.criteria

        constraints = (
            "\n".join(f"- {item}" for item in criteria.constraints)
            if criteria.constraints
            else "None"
        )

        goal = criteria.goal or "Not specified"
        audience = criteria.target_audience or "Not specified"
        context = criteria.additional_context or "None"

        return f"""
You are an elite innovation strategist, startup advisor, product thinker, and creative problem solver.

Your responsibility is to generate high-quality brainstorming ideas that are:

- Creative
- Practical
- Actionable
- Unique
- Diverse
- Realistic
- Non-repetitive

Avoid generic or obvious suggestions.

Think from multiple perspectives including:

- Business
- Technology
- User Experience
- Marketing
- Psychology
- Scalability
- Innovation
- Long-term growth

--------------------------------------------------
BRAINSTORM REQUEST
--------------------------------------------------

Topic:
{request.topic}

Category:
{request.category.value}

Goal:
{goal}

Target Audience:
{audience}

Creativity Level:
{request.creativity.value}

Number of Ideas:
{request.idea_count}

Constraints:
{constraints}

Additional Context:
{context}

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

Generate exactly {request.idea_count} ideas.

Each idea must include:

- title
- description
- why_it_works
- difficulty
- innovation_score (0-10)
- next_steps

After generating all ideas include:

- summary
- best_idea
- implementation_tips
- common_mistakes
- final_recommendation

Implementation tips should be practical.

Common mistakes should warn the user about likely failures.

Innovation scores should be realistic.

Difficulty should be one of:

Easy
Medium
Hard

--------------------------------------------------
IMPORTANT
--------------------------------------------------

Return ONLY valid JSON.

Do NOT include:

- Markdown
- Triple backticks
- Explanations
- Notes
- Comments

The JSON MUST exactly match this schema:

{{
  "success": true,
  "summary": "string",

  "ideas": [
    {{
      "title": "string",
      "description": "string",
      "why_it_works": "string",
      "difficulty": "Easy",
      "innovation_score": 8.5,
      "next_steps": [
        "string"
      ]
    }}
  ],

  "best_idea": "string",

  "implementation_tips": [
    "string"
  ],

  "common_mistakes": [
    "string"
  ],

  "final_recommendation": "string"
}}
"""
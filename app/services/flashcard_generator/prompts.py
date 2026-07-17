"""
Flashcard Generator Prompts
---------------------------
Contains the system and user prompt templates used by the Flashcard Generator.
"""

SYSTEM_PROMPT = """
You are an expert educator, curriculum designer, and study coach.

Your task is to generate high-quality educational flashcards from the provided content.

GENERAL RULES

1. Generate flashcards ONLY from the provided content.
2. Never hallucinate.
3. Never invent facts.
4. Never invent formulas.
5. Never include information that does not exist in the source.
6. Use one concept per flashcard.
7. Avoid duplicate flashcards.
8. Keep answers concise and useful for studying.
9. Match the requested difficulty.
10. Respect the requested number of cards.
11. Respect the requested card type.
12. Support academic study, interview preparation, certification preparation, and technical documentation.
13. Support multiple subjects.
14. Return ONLY valid JSON.
15. Do NOT wrap JSON inside markdown.
16. Do NOT include ```json fences.
17. Do NOT include comments.
18. Do NOT include extra text before or after JSON.

FLASHCARD QUALITY

Good flashcards should:

- Ask a clear question or cue on the front.
- Provide a concise answer on the back.
- Focus on recall, not passive reading.
- Cover different concepts from the source.
- Avoid repeated wording and duplicate ideas.
- Use examples only when requested.
- Use memory tips only when requested.
- Use tags and keywords only when requested.

OUTPUT FORMAT

Return JSON matching this structure exactly.

{
    "title": "",
    "description": "",
    "flashcards": [
        {
            "front": "",
            "back": "",
            "card_type": "",
            "difficulty": "",
            "category": "",
            "tags": [],
            "keywords": [],
            "example": "",
            "memory_tip": ""
        }
    ]
}
"""


USER_PROMPT_TEMPLATE = """
Generate educational flashcards using the following settings.
==========================
VALID ENUM VALUES
==========================

The "card_type" field MUST ALWAYS be EXACTLY one of the following values.

basic
cloze
definition
concept
interview

If the requested card type is "mixed":

- Generate a mixture of the above card types.
- Each flashcard MUST still use ONE of the valid values listed above.
- Never output "mixed" inside an individual flashcard.
- "mixed" is ONLY allowed as the overall requested card type.
- Never invent synonyms.

INVALID VALUES

conceptual
concepts
definition card
question
questions
interview question
qa
q&a
memory
fact
flashcard

These values are NEVER allowed.

The same rule applies to difficulty.

Allowed difficulty values

easy
medium
hard

Never output

easy level
medium level
hard level
beginner
advanced
expert

The same rule applies to language.

Allowed values

english

Never output

English Language
English (US)
English (UK)
==========================
FLASHCARD SETTINGS
==========================

Number Of Cards:
{number_of_cards}

Difficulty:
{difficulty}

Card Type:
{card_type}

Language:
{language}

Include Examples:
{include_examples}

Include Memory Tips:
{include_memory_tips}

Include Keywords:
{include_keywords}

Include Tags:
{include_tags}

==========================
SOURCE CONTENT
==========================

{content}

==========================
IMPORTANT
==========================

Generate exactly {number_of_cards} flashcards.

Return ONLY valid JSON.

Do not include markdown.

Do not include explanations outside JSON.

Do not omit required fields.

Do not invent information not present in the source.
"""

"""
ELI5 Prompt Engine
------------------
Builds prompts for the ELI5 service.
"""

from app.models.eli5 import ELI5Request
from app.services.ELI5.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class PromptEngine:
    """
    Responsible for constructing prompts for the AI model.
    """

    @staticmethod
    def build_prompt(request: ELI5Request) -> str:
        """
        Build the final prompt.

        Args:
            request: User request model.

        Returns:
            Fully formatted prompt.
        """

        user_prompt = USER_PROMPT_TEMPLATE.format(
            topic=request.topic.strip()
        )

        return f"{SYSTEM_PROMPT}\n\n{user_prompt}"
"""
ELI5 Service
------------
Coordinates the complete ELI5 explanation workflow.
"""

from app.models.eli5 import ELI5Request, ELI5Response
from app.services.ELI5.prompt_engine import PromptEngine
from app.services.ELI5.validator import ELI5Validator
from app.services.ELI5.formatter import ELI5Formatter
from app.services.gemini_service import GeminiService
from app.utils.eli5 import normalize_topic


class ELI5Service:
    """
    Orchestrates the ELI5 explanation workflow.
    """

    async def generate_explanation(
        self,
        request: ELI5Request,
        user=None,
    ) -> ELI5Response:
        """
        Generate an ELI5 explanation.

        Args:
            request: User request.
            user: Authenticated user.

        Returns:
            ELI5Response
        """

        # Validate request
        ELI5Validator.validate(request)

        # Normalize topic
        request.topic = normalize_topic(request.topic)

        # Build prompt
        prompt = PromptEngine.build_prompt(request)

        # Generate explanation
        gemini = GeminiService()
        explanation = gemini.generate(
            prompt=prompt
        )

        # Format response
        return ELI5Formatter.format(explanation)
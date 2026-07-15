from app.models.youtube_summarizer import YouTubeSummaryRequest
from app.services.youtube_summarizer.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class PromptEngine:
    """
    Responsible for constructing prompts for the
    YouTube Summarizer.
    """

    @staticmethod
    def build_system_prompt() -> str:
        """
        Return the system prompt.
        """

        return SYSTEM_PROMPT.strip()

    @staticmethod
    def build_user_prompt(
        transcript: str,
        request: YouTubeSummaryRequest,
    ) -> str:
        """
        Build the user prompt using the cleaned transcript
        and user-selected settings.
        """

        return USER_PROMPT_TEMPLATE.format(
            style=request.settings.style.value.replace("_", " ").title(),
            length=request.settings.length.value.title(),
            tone=request.settings.tone.value.title(),
            language=request.settings.language,
            transcript=transcript.strip(),
        ).strip()

    @classmethod
    def build_prompt(
        cls,
        transcript: str,
        request: YouTubeSummaryRequest,
    ) -> str:
        """
        Build the complete prompt for Gemini.
        """

        return (
            f"{cls.build_system_prompt()}\n\n"
            f"{cls.build_user_prompt(transcript, request)}"
        )
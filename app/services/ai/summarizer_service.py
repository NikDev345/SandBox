from sqlalchemy.orm import Session
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService

print("ToolService imported from:", ToolService.__module__)
print("Methods:", dir(ToolService))

class SummarizerService:
    """
    Business logic for AI Text Summarizer.
    """

    @staticmethod
    def summarize(
        db: Session,
        user_id: str,
        text: str,
        length: str,
    ) -> str:

        # -------------------------
        # Validate Input
        # -------------------------

        text = text.strip()

        if not text:
            raise ValueError("Text cannot be empty.")

        # -------------------------
        # Build Prompt
        # -------------------------

        prompt = PromptEngine.build_summary_prompt(
            text=text,
            length=length,
        )

        # -------------------------
# Get Tool
# -------------------------

        tool = ToolService.get_tool_by_slug(
        db=db,
        slug="TEXT-SUMMARIZER",
        )

        if tool is None:
         raise ValueError("Text Summarizer tool is not registered.")

# -------------------------
# Generate Summary
# -------------------------

        gemini = GeminiService()

        summary = gemini.generate(prompt)

# -------------------------
# Save Execution History
# -------------------------

        ExecutionService.create_execution(
            db=db,
            user_id=user_id,
            tool_id=tool.id,
            user_input=text,
            output=summary,
        )
        # -------------------------
        # Return Summary
        # -------------------------

        return summary
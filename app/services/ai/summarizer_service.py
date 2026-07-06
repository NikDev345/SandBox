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
        instructions: str | None = None,
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
            instructions=instructions,
        )

        # -------------------------
# Get Tool
# -------------------------

        tool = ToolService.get_tool_by_slug(
        db=db,
        slug="TEXT-SUMMARIZER",
        )
        if tool is None:
            # In local/dev environments the tool registry may not be populated.
            # Fall back to a placeholder tool id so summaries can still be generated
            # and execution history saved under a generic id.
            tool_id = "TEXT-SUMMARIZER"
        else:
            tool_id = tool.id

# -------------------------
# Generate Summary
# -------------------------

        gemini = GeminiService()

        summary = gemini.generate(prompt)

# -------------------------
# Save Execution History
# -------------------------

        # Save execution history where possible. Use fallback tool_id when needed.
        try:
            ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=text,
                output=summary,
            )
        except Exception:
            # don't block returning the summary if history save fails in dev
            pass
        # -------------------------
        # Return Summary
        # -------------------------

        return summary
from sqlalchemy.orm import Session
from app.services.gemini_service import GeminiService
from app.services.prompt_engine import PromptEngine
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
import json

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
        slug="text_summarizer",
        )
        if tool is None:
            # In local/dev environments the tool registry may not be populated.
            # Fall back to a placeholder tool id so summaries can still be generated
            # and execution history saved under a generic id.
            tool_id = "text_summarizer"
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
        execution_id: str | None = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=json.dumps({"text": text, "length": length, "instructions": instructions,}),
                output=summary,
            )
            execution_id = execution.id 
        except Exception:
            # don't block returning the summary if history save fails in dev
            pass
        # -------------------------
        # Return Summary
        # -------------------------

        return summary, execution_id
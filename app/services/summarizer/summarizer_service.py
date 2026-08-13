from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.services.prompt_engine import PromptEngine


class SummarizerService:
    """
    Business logic for AI Text Summarizer.

    Heavy AI / execution dependencies are imported lazily
    so they do not slow down application startup.
    """

    @staticmethod
    async def summarize(
        db: Session,
        user_id: str,
        text: str,
        length: str,
        instructions: str | None = None,
    ):

        # ====================================================
        # VALIDATE
        # ====================================================

        text = text.strip()

        if not text:
            raise ValueError(
                "Text cannot be empty."
            )

        if length not in {
            "short",
            "medium",
            "detailed",
        }:
            raise ValueError(
                "Invalid summary length."
            )

        # ====================================================
        # BUILD PROMPT
        # ====================================================

        prompt = PromptEngine.build_summary_prompt(
            text=text,
            length=length,
            instructions=instructions,
        )

        # ====================================================
        # LAZY AI IMPORT
        # ====================================================

        from app.services.LLM_Gateway.llm_config import (
            gateway,
        )

        from app.models.gateway import LLMRequest

        # ====================================================
        # GENERATE
        # ====================================================

        result = await gateway.generate(
            LLMRequest(
                prompt=prompt,
                tool_slug="text_summarizer",
                temperature=0.5,
            )
        )

        if not result or not result.text:
            raise RuntimeError(
                "AI returned an empty summary."
            )

        summary = result.text.strip()

        # ====================================================
        # SAVE EXECUTION
        # ====================================================

        execution_id = None

        try:

            # Lazy imports
            from app.services.tool_executor import (
                ExecutionService,
            )

            from app.services.tool_service import (
                ToolService,
            )

            tool = ToolService.get_tool_by_slug(
                db=db,
                slug="text_summarizer",
            )

            # Only save history when the real tool exists.
            #
            # This avoids creating executions with a fake
            # "text_summarizer" tool ID.
            if tool:

                user_input = json.dumps(
                    {
                        "text": text,
                        "length": length,
                        "instructions": instructions,
                    },
                    ensure_ascii=False,
                )

                execution = (
                    ExecutionService.create_execution(
                        db=db,
                        user_id=user_id,
                        tool_id=tool.id,
                        user_input=user_input,
                        output=summary,
                    )
                )

                execution_id = execution.id

        except Exception as exc:

            # History failure must not destroy a successfully
            # generated summary.
            print(
                "[SUMMARIZER] Execution history failed:",
                repr(exc),
            )

        # ====================================================
        # RETURN
        # ====================================================

        return summary, execution_id
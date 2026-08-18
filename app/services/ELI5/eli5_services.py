"""
ELI5 Service
------------
Coordinates the complete ELI5 explanation workflow.

Heavy AI and execution dependencies are loaded lazily
when the service is actually executed.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.eli5 import (
    ELI5Request,
    ELI5Response,
)


class ELI5Service:
    """
    Orchestrates the ELI5 explanation workflow.
    """

    async def generate_explanation(
        self,
        request: ELI5Request,
        db: Session,
        user=None,
    ) -> ELI5Response:
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user['sub'])

        # ====================================================
        # LAZY BUSINESS LOGIC IMPORTS
        # ====================================================

        from app.services.ELI5.prompt_engine import (
            PromptEngine,
        )

        from app.services.ELI5.validator import (
            ELI5Validator,
        )

        from app.services.ELI5.formatter import (
            ELI5Formatter,
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        ELI5Validator.validate(request)

        # ====================================================
        # NORMALIZE TOPIC
        # ====================================================

        from app.utils.eli5 import normalize_topic

        request.topic = normalize_topic(
            request.topic
        )

        # ====================================================
        # BUILD PROMPT
        # ====================================================

        prompt = PromptEngine.build_prompt(
            request
        )

        # ====================================================
        # LAZY AI GATEWAY IMPORT
        # ====================================================

        from app.services.LLM_Gateway.llm_config import (
            gateway,
        )

        from SandBox.app.router_llm.gateway import (
            LLMRequest,
        )

        # ====================================================
        # GENERATE EXPLANATION
        # ====================================================

        llm_request = LLMRequest(
            prompt=prompt,
            temperature=0.6,
            max_output_tokens=8000,
            tool_slug="eli5",
        )

        response = await gateway.generate(
            llm_request
        )

        if not response or not response.text:

            raise RuntimeError(
                "Empty response from LLM Gateway."
            )

        explanation = response.text.strip()

        # ====================================================
        # FORMAT RESPONSE
        # ====================================================

        formatted_response = (
            ELI5Formatter.format(
                explanation
            )
        )

        # ====================================================
        # SAVE EXECUTION HISTORY
        # ====================================================

        execution_id = None

        try:

            # ------------------------------------------------
            # Lazy imports
            # ------------------------------------------------

            from app.services.tool_service import (
                ToolService,
            )

            from app.services.tool_executor import (
                ExecutionService,
            )

            # ------------------------------------------------
            # Find tool
            # ------------------------------------------------

            tool = ToolService.get_tool_by_slug(
                db=db,
                slug="eli5",
            )

            if tool:

                execution = (
                    ExecutionService.create_execution(
                        db=db,
                        user_id=user["sub"],
                        tool_id=tool.id,
                        user_input=request.model_dump_json(),
                        output=explanation,
                    )
                )

                execution_id = execution.id

        except Exception as exc:

            # History failure should never destroy
            # a successfully generated explanation.

            print(
                "[ELI5] Execution history failed:",
                repr(exc),
            )

        # ====================================================
        # ATTACH EXECUTION ID
        # ====================================================

        formatted_response.execution_id = (
            execution_id
        )

        return formatted_response
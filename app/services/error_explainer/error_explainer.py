"""
Error Explainer Service
----------------------
Explains errors using LLM with support for:
• Structured output (Pydantic schema)
• Large input handling via temp files (1500+ chars)
• Execution tracking
"""

from __future__ import annotations

import json
import tempfile
import textwrap
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from pydantic import ValidationError

from google.genai import types

from app.models.error_explainer import (
    ErrorExplainerRequest,
    ErrorExplainerResponse,
)

from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
from app.services.credit_service import enforce_credit_limit


class ErrorExplainer:
    """
    Handles full error explanation pipeline.
    """

    THRESHOLD = 1500  # chars

    # ====================================================
    # INPUT VALIDATION + FILE HANDLING
    # ====================================================

    @staticmethod
    def _create_temp_file(content: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(content)
            return temp_file.name

    @classmethod
    def _prepare_input(
        cls,
        request: ErrorExplainerRequest,
    ) -> Tuple[str, Optional[str], bool, Optional[str], Optional[str]]:

        if not request.error or not request.error.strip():
            raise ValueError("Error is required")

        error = request.error.strip()
        code = request.code.strip() if request.code else None

        error_file_path = None
        code_file_path = None

        # Use file if exceeds threshold
        if len(error) > cls.THRESHOLD:
            error_file_path = cls._create_temp_file(error)

        if code and len(code) > cls.THRESHOLD:
            code_file_path = cls._create_temp_file(code)

        use_file = bool(error_file_path or code_file_path)

        return error, code, use_file, error_file_path, code_file_path

    # ====================================================
    # PROMPT
    # ====================================================

    @staticmethod
    def _build_prompt() -> str:
        return textwrap.dedent("""
You are an expert software debugging assistant.

Analyze the provided error and optional source code.

Return ONLY valid JSON:

{
  "title": "string",
  "explanation": "string",
  "code": "string | null"
}

Rules:
- No markdown
- No extra text
- Strict JSON only
""")

    # ====================================================
    # AI CALL
    # ====================================================

    @staticmethod
    async def _call_ai(
        prompt: str,
        error: str,
        code: Optional[str],
        use_file: bool,
        error_file_path: Optional[str],
        code_file_path: Optional[str],
    ) -> dict:

        contents = []

        # -------- FILE MODE --------
        if use_file:
            if error_file_path:
                with open(error_file_path, "rb") as f:
                    contents.append(
                        types.Part.from_bytes(
                            data=f.read(),
                            mime_type="text/plain",
                        )
                    )

            if code_file_path:
                with open(code_file_path, "rb") as f:
                    contents.append(
                        types.Part.from_bytes(
                            data=f.read(),
                            mime_type="text/plain",
                        )
                    )

            user_prompt = prompt

            if not error_file_path:
                user_prompt += f"\n\n### ERROR ###\n{error}"

            if code and not code_file_path:
                user_prompt += f"\n\n### CODE ###\n{code}"

        # -------- TEXT MODE --------
        else:
            user_prompt = f"{prompt}\n\n### ERROR ###\n{error}"

            if code:
                user_prompt += f"\n\n### CODE ###\n{code}"

        # -------- LLM REQUEST --------
        llm_response = await gateway.generate(
            LLMRequest(
                prompt=user_prompt,
                contents=contents,  # empty if text mode
                temperature=0.2,
                max_output_tokens=4000,
                response_mime_type="application/json",
                tool_slug="error_explainer",
                response_schema=ErrorExplainerResponse,
                cache=False,
            )
        )

        if not llm_response or not llm_response.text:
            raise RuntimeError("Empty response from LLM")

        if not isinstance(llm_response.text, dict):
            raise RuntimeError("Invalid structured response")

        return llm_response.text

    # ====================================================
    # MAIN SERVICE
    # ====================================================

    @staticmethod
    async def explain_error(
        request: ErrorExplainerRequest,
        user_id: str,
        db: Session,
    ) -> ErrorExplainerResponse:

        # ---- Credit check ----
        enforce_credit_limit(db, user_id)

        # ---- Prepare input ----
        (
            error,
            code,
            use_file,
            error_file_path,
            code_file_path,
        ) = ErrorExplainer._prepare_input(request)

        # ---- Prompt ----
        prompt = ErrorExplainer._build_prompt()

        # ---- AI Call ----
        raw_data = await ErrorExplainer._call_ai(
            prompt=prompt,
            error=error,
            code=code,
            use_file=use_file,
            error_file_path=error_file_path,
            code_file_path=code_file_path,
        )

        # ---- Validate response ----
        try:
            data = ErrorExplainerResponse(**raw_data)
        except ValidationError as e:
            raise RuntimeError(f"Invalid AI response format: {e}")

        # ---- Save execution ----
        execution_id = None
        try:
            tool = ToolService.get_tool_by_slug(
                db=db,
                slug="error_explainer",
            )

            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool.id if tool else "error_explainer",
                user_input=request.model_dump_json(),
                output=json.dumps(data.model_dump()),
            )

            execution_id = execution.id

        except Exception:
            pass  # do not break flow

        data.execution_id = execution_id
        return data
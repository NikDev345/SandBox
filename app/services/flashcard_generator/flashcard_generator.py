"""
Flashcard Generator Service
---------------------------
Production-grade version with structured LLM output.
"""

from __future__ import annotations

import random
import re
import unicodedata
import json

from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.models.flashcard_generator import (
    FlashcardGeneratorRequest,
    FlashcardGeneratorResponse,
    FlashcardGeneratorLLMResponse,  # <-- ADD THIS MODEL
)

from app.services.flashcard_generator.formatter import (
    FlashcardGeneratorFormatter,
)

from app.services.flashcard_generator.prompt_engine import (
    PromptEngine,
)

from app.services.flashcard_generator.validator import (
    FlashcardGeneratorValidator,
)

from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest

from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService


class FlashcardGeneratorService:

    @staticmethod
    async def generate(
        request: FlashcardGeneratorRequest,
        db: Session,
        user=None,
    ) -> FlashcardGeneratorResponse:

        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user["sub"])

        # ====================================================
        # VALIDATION
        # ====================================================
        FlashcardGeneratorValidator.validate_request(request)

        # ====================================================
        # PREPROCESS
        # ====================================================
        cleaned_request = FlashcardGeneratorService._preprocess(request)

        # ====================================================
        # PROMPT
        # ====================================================
        prompt = PromptEngine.build_prompt(cleaned_request)

        # ====================================================
        # LLM CALL (STRUCTURED)
        # ====================================================
        llm_response = await gateway.generate(
            LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=10000,
                tool_slug="flashcard_generator",
                response_schema=FlashcardGeneratorLLMResponse,
            )
        )

        if not llm_response or not llm_response.text:
            raise RuntimeError("Empty response from LLM")

        if not isinstance(llm_response.text, dict):
            raise RuntimeError("Invalid structured response")

        # ====================================================
        # PARSE STRUCTURED OUTPUT
        # ====================================================
        try:
            data = FlashcardGeneratorLLMResponse(**llm_response.text)
        except ValidationError as e:
            raise RuntimeError(f"Invalid AI response format: {e}")

        # ====================================================
        # FORMAT RESPONSE
        # ====================================================
        response = FlashcardGeneratorFormatter.format(
            data.model_dump(),
            cleaned_request.settings,
        )

        # ====================================================
        # SHUFFLE (OPTIONAL)
        # ====================================================
        if cleaned_request.settings.shuffle_cards:
            random.shuffle(response.result.flashcards)

        # ====================================================
        # VALIDATE FINAL RESPONSE
        # ====================================================
        FlashcardGeneratorService._validate_response(
            response,
            cleaned_request,
        )

        # ====================================================
        # SAVE EXECUTION
        # ====================================================
        execution_id = None
        try:
            tool = ToolService.get_tool_by_slug(
                db=db,
                slug="flashcard_generator",
            )

            execution = ExecutionService.create_execution(
                db=db,
                user_id=user["sub"],
                tool_id=tool.id if tool else "flashcard_generator",
                user_input=request.model_dump_json(),
                output=json.dumps(data.model_dump()),
            )

            execution_id = execution.id

        except Exception:
            pass

        response.execution_id = execution_id
        return response

    # ====================================================
    # PREPROCESS
    # ====================================================

    @staticmethod
    def _preprocess(
        request: FlashcardGeneratorRequest,
    ) -> FlashcardGeneratorRequest:

        content = FlashcardGeneratorService._clean_text(
            request.content
        )

        return FlashcardGeneratorRequest(
            content=content,
            settings=request.settings,
        )

    @staticmethod
    def _clean_text(text: str) -> str:

        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)

        text = text.replace("```json", "").replace("```", "")

        text = "".join(
            ch
            for ch in text
            if ch in ("\n", "\t")
            or unicodedata.category(ch)[0] != "C"
        )

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = [line.strip() for line in text.split("\n")]

        cleaned_lines = []
        previous_blank = False

        for line in lines:
            if line == "":
                if previous_blank:
                    continue
                previous_blank = True
            else:
                previous_blank = False

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    # ====================================================
    # VALIDATION
    # ====================================================

    @staticmethod
    def _validate_response(
        response: FlashcardGeneratorResponse,
        request: FlashcardGeneratorRequest,
    ):

        try:
            FlashcardGeneratorValidator.validate_response(
                response,
                request,
            )
        except ValidationError as exc:
            raise RuntimeError(
                "AI response validation failed."
            ) from exc
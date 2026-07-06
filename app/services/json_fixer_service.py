import json
import re
from json_repair import repair_json
from sqlalchemy.orm import Session
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService


class JSONFixerService:
    """
    Business logic for JSON Fixer.
    """

    @staticmethod
    def fix_json(
        db: Session,
        user_id: str,
        json_text: str,
    ) -> dict:
        # -------------------------
        # Validate Input
        # -------------------------
        json_text = json_text.strip()
        if not json_text:
            raise ValueError("JSON input cannot be empty.")

        repairs = []
        original_text = json_text

        # -------------------------
        # Remove Markdown Code Fences
        # -------------------------
        if json_text.startswith("```"):
            lines = json_text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_text = "\n".join(lines).strip()
            repairs.append("Removed Markdown code fences")

        # -------------------------
        # Detect Common Issues
        # -------------------------

        # Single quotes used as string delimiters
        if re.search(r"'[^']*'\s*:", original_text) or re.search(r":\s*'[^']*'", original_text):
            repairs.append("Converted single quotes to double quotes")

        # Unquoted object keys — bare word directly after { or , or newline
        if re.search(r'(?:^|[{,\n])\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', original_text):
            repairs.append("Added quotes around object keys")

        # Trailing commas before } or ]
        if re.search(r',\s*[}\]]', original_text):
            repairs.append("Removed trailing commas")

        # JS-style comments
        if "//" in original_text or "/*" in original_text:
            repairs.append("Removed comments")

        # -------------------------
        # Repair JSON
        # -------------------------
        try:
            repaired_json = repair_json(json_text)
        except Exception:
            raise ValueError("Failed to repair JSON.")

        # -------------------------
        # Validate Repaired JSON
        # -------------------------
        try:
            parsed_json = json.loads(repaired_json)
        except json.JSONDecodeError:
            raise ValueError("Unable to repair the provided JSON.")

        # -------------------------
        # Pretty Format
        # -------------------------
        formatted_json = json.dumps(
            parsed_json,
            indent=2,
            ensure_ascii=False,
        )
        repairs.append("Pretty formatted JSON")

        # Remove duplicates while preserving insertion order
        repairs = list(dict.fromkeys(repairs))

        # -------------------------
        # Get Tool
        # -------------------------
        tool = ToolService.get_tool_by_slug(
            db=db,
            slug="JSON-FIXER",
        )
        tool_id = tool.id if tool else "JSON-FIXER"

        # -------------------------
        # Save Execution History
        # -------------------------
        try:
            ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=original_text,
                output=formatted_json,
            )
        except Exception:
            pass

        # -------------------------
        # Return Result
        # -------------------------
        return {
            "success": True,
            "message": "JSON repaired successfully.",
            "fixed_json": formatted_json,
            "repairs": repairs,
        }
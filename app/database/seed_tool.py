from sqlalchemy.orm import Session

from app.models.tool import Tools
from app.services.tool_service import ToolService


def seed_tools(db: Session):

    tools = [
        {
            "name": "JSON Fixer",
            "category": "Developer Tools",
            "description": "Repair malformed JSON and format it into valid JSON.",
            "icon_url": "/assets/icons/json-fixer.svg",
            "source_path": "app/services/json_fixer_service.py",
        },
    ]

    for tool in tools:

        existing = ToolService.get_tool_by_slug(
            db,
            tool["name"].upper().replace(" ", "-"),
        )

        if existing:
            continue

        ToolService.create_tool(
            db=db,
            **tool,
        )
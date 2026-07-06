from sqlalchemy.orm import Session

from app.services.tool_service import ToolService


DEFAULT_TOOLS = [

    {
        "name": "AI Text Summarizer",
        "category": "AI",
        "description": "Generate concise AI-powered summaries from text or documents.",
        "icon_url": "/assets/icons/text_summarizer.svg",
        "source_path": "text_summarizer",
    },

    {
        "name": "JSON Fixer",
        "category": "Developer Tools",
        "description": "Repair and format malformed JSON instantly.",
        "icon_url": "/assets/icons/json_fixer.svg",
        "source_path": "json_fixer",
    },

]


def seed_tools(db: Session):

    print("🌱 Seeding tools...")

    for tool in DEFAULT_TOOLS:

        slug = tool["name"].strip().upper().replace(" ", "-")

        existing = ToolService.get_tool_by_slug(
            db=db,
            slug=slug,
        )

        if existing:

            print(f"   • {tool['name']} (exists)")

            continue

        ToolService.create_tool(
            db=db,
            name=tool["name"],
            category=tool["category"],
            description=tool["description"],
            icon_url=tool["icon_url"],
            source_path=tool["source_path"],
        )

        print(f"   ✓ {tool['name']} (added)")

    print("✓ Tool seeding complete.\n")
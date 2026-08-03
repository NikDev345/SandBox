from sqlalchemy.orm import Session

from app.services.tool_service import ToolService


DEFAULT_TOOLS = [
    {
        "name": "AI Text Summarizer",
        "category": "Content Tool",
        "description": "Generate concise AI-powered summaries from text or documents.",
        "icon_url": "/assets/icons/text_summarizer.svg",
        "source_path": "/text-summarizer",
    },
    {
        "name": "JSON Fixer",
        "category": "Developer Tools",
        "description": "Repair and format malformed JSON instantly.",
        "icon_url": "/assets/icons/json_fixer.svg",
        "source_path": "/json-fixer",
    },
    {
        "name": "Blog Outline Generator",
        "category": "Content Tools",
        "description": "Generate structured blog outlines for any topic.",
        "icon_url": "/assets/icons/blog_generator.svg",
        "source_path": "/blog-outline-generator",
    },
    {
        "name": "Brainstorm Generator",
        "category": "Productivity Tools",
        "description": "Generate creative ideas, concepts, and brainstorming suggestions.",
        "icon_url": "/assets/icons/brainstorm_generator.svg",
        "source_path": "/brainstorm-generator",
    },
    {
        "name": "Chart Explainer",
        "category": "Image Tool",
        "description": "Explain charts, graphs, and data visualizations in simple language.",
        "icon_url": "/assets/icons/chart_explainer.svg",
        "source_path": "/chart-explainer",
    },
    {
        "name": "Code Reviewer",
        "category": "Developer Tool",
        "description": "Analyze source code and provide review, improvements, and best practices.",
        "icon_url": "/assets/icons/code_reviewer.svg",
        "source_path": "/code",
    },
    {
        "name": "Commit Message Generator",
        "category": "Developer Tool",
        "description": "Generate meaningful Git commit messages from code changes.",
        "icon_url": "/assets/icons/commit_msg.svg",
        "source_path": "/commit-gen",
    },
    {
        "name": "Decision Maker",
        "category": "Productivity Tool",
        "description": "Evaluate options and help make informed decisions.",
        "icon_url": "/assets/icons/decision_maker.svg",
        "source_path": "/decision-maker",
    },
    {
        "name": "Docker Generator",
        "category": "Developer Tool",
        "description": "Generate optimized Dockerfiles for your applications.",
        "icon_url": "/assets/icons/docker_generator.svg",
        "source_path": "/docker",
    },
    {
        "name": "ELI5 Explainer",
        "category": "Content Tool",
        "description": "Explain complex concepts in simple, easy-to-understand language.",
        "icon_url": "/assets/icons/eli5.svg",
        "source_path": "/eli5",
    },
    {
        "name": "Email Rewriter",
        "category": "Productivity Tool",
        "description": "Rewrite emails with improved clarity, tone, and professionalism.",
        "icon_url": "/assets/icons/email_rewriter.svg",
        "source_path": "/email-rewriter",
    },
    {
        "name": "Error Explainer",
        "category": "Developer Tool",
        "description": "Explain programming errors and suggest possible fixes.",
        "icon_url": "/assets/icons/error_explainer.svg",
        "source_path": "/error",
    },
    {
        "name": "Flashcard Generator",
        "category": "Content Tool",
        "description": "Generate study flashcards from notes or documents.",
        "icon_url": "/assets/icons/flashcard_generator.svg",
        "source_path": "/flashcard-generator",
    },
    {
        "name": "Item Extractor",
        "category": "Productivity Tool",
        "description": "Extract important tasks, items, or action points from text.",
        "icon_url": "/assets/icons/item_extractor.svg",
        "source_path": "/item",
    },
    {
        "name": "Mock API Generator",
        "category": "Developer Tool",
        "description": "Generate realistic mock API responses from API specifications.",
        "icon_url": "/assets/icons/mock_api.svg",
        "source_path": "/mock_api",
    },
    {
        "name": "Notes Cleaner",
        "category": "Productivity Tool",
        "description": "Clean, organize, and format messy notes into structured content.",
        "icon_url": "/assets/icons/notes_cleaner.svg",
        "source_path": "/notes_cleaner",
    },
    {
        "name": "Image Text Extractor",
        "category": "Image Tool",
        "description": "Extract text from images using AI-powered OCR.",
        "icon_url": "/assets/icons/image_text_extractor.svg",
        "source_path": "/image-text-extractor",
    },
    {
        "name": "Quiz Generator",
        "category": "Content Tool",
        "description": "Generate quizzes from text, notes, or documents.",
        "icon_url": "/assets/icons/quiz_generator.svg",
        "source_path": "/quiz-generator",
    },
    {
        "name": "Pros & Cons Generator",
        "category": "Productivity Tool",
        "description": "Generate balanced pros and cons for any decision or idea.",
        "icon_url": "/assets/icons/pro_cons.svg",
        "source_path": "/pro_cons_gen",
    },
    {
        "name": "Regex Generator",
        "category": "Developer Tool",
        "description": "Generate regular expressions from natural language descriptions.",
        "icon_url": "/assets/icons/regex_generator.svg",
        "source_path": "/regex-gen",
    },
    {
        "name": "SQL Generator",
        "category": "Developer Tool",
        "description": "Generate SQL queries from natural language requests.",
        "icon_url": "/assets/icons/sql_generator.svg",
        "source_path": "/sql-gen",
    },
    {
        "name": "Screenshot Explainer",
        "category": "Image Tool",
        "description": "Explain screenshots, interfaces, and visual content using AI.",
        "icon_url": "/assets/icons/ss_explainer.svg",
        "source_path": "/ss_explain",
    },
    {
        "name": "Table Extractor",
        "category": "Image Tool",
        "description": "Extract structured tables from images or PDF documents.",
        "icon_url": "/assets/icons/table_extractor.svg",
        "source_path": "/table-extractor",
    },
    {
        "name": "YAML Generator",
        "category": "Developer Tool",
        "description": "Generate YAML configurations from natural language.",
        "icon_url": "/assets/icons/yaml_generator.svg",
        "source_path": "/yaml",
    },
    {
        "name": "YouTube Summarizer",
        "category": "Content Tool",
        "description": "Generate concise summaries of YouTube videos.",
        "icon_url": "/assets/icons/youtube_summarizer.svg",
        "source_path": "/youtube-summarizer",
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
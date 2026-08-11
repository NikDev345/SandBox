import html
import json
import os
from urllib.parse import urljoin

from nicegui import ui


CANONICAL_BASE_URL = "https://sandboxhome.online"
SITE_NAME = "SandBox"
DEFAULT_IMAGE_PATH = "/assets/logo.png"


def _base_url() -> str:
    return (os.getenv("APP_BASE_URL") or CANONICAL_BASE_URL).rstrip("/")


def absolute_url(path: str = "/") -> str:
    return urljoin(f"{_base_url()}/", path.lstrip("/"))


def _meta_attrs(attrs: dict[str, str]) -> str:
    return " ".join(
        f'{name}="{html.escape(value, quote=True)}"'
        for name, value in attrs.items()
    )


def _tag(name: str, attrs: dict[str, str]) -> str:
    return f"<{name} {_meta_attrs(attrs)}>"


PUBLIC_PAGES = {
    "/": {
        "title": "SandBox - AI Tools for Developers, Students & Creators",
        "description": "SandBox brings AI-powered tools for developers, students, and creators into one workspace, including SQL generation, JSON repair, code review, summaries, quizzes, and content helpers.",
    },
    "/json-fixer": {
        "title": "JSON Fixer - Repair Invalid JSON Online | SandBox",
        "description": "Fix malformed JSON, clean syntax errors, and turn broken JSON into a usable format with SandBox's AI JSON Fixer.",
    },
    "/text-summarizer": {
        "title": "Text Summarizer - Summarize PDFs and Text | SandBox",
        "description": "Summarize pasted text or PDF content into clear, structured notes with SandBox's AI Text Summarizer.",
    },
    "/image-text-extractor": {
        "title": "Image Text Extractor - OCR from Images | SandBox",
        "description": "Extract readable text from images with SandBox's AI Image Text Extractor and turn screenshots or photos into usable text.",
    },
    "/eli5": {
        "title": "ELI5 Explainer - Explain Complex Topics Simply | SandBox",
        "description": "Turn complex ideas into simple explanations with SandBox's ELI5 tool for students, creators, and curious learners.",
    },
    "/ss_explain": {
        "title": "Screenshot Explainer - Understand Images with AI | SandBox",
        "description": "Upload a screenshot and get a clear AI explanation of the visual content, interface, chart, error, or document.",
    },
    "/sql_gen": {
        "title": "SQL Generator - Create SQL from Plain English | SandBox",
        "description": "Generate SQL queries from natural language prompts with SandBox's AI SQL Generator for faster database work.",
    },
    "/table_extractor": {
        "title": "AI Table Extractor - Extract Tables from PDFs and Images | SandBox",
        "description": "Extract structured tables from PDFs and images, then export results as Excel, CSV, or JSON with SandBox.",
    },
    "/notes_cleaner": {
        "title": "Notes Cleaner - Clean and Organize Notes | SandBox",
        "description": "Clean messy notes, improve readability, and organize study or work material with SandBox's AI Notes Cleaner.",
    },
    "/mock_api": {
        "title": "Mock API Generator - Create Fake API Endpoints | SandBox",
        "description": "Create realistic mock API endpoints for testing, prototyping, and frontend development with SandBox.",
    },
    "/chart-explainer": {
        "title": "Chart Explainer - Explain Charts with AI | SandBox",
        "description": "Upload or describe a chart and get a clear explanation of trends, patterns, and insights with SandBox.",
    },
    "/email-rewriter": {
        "title": "Email Rewriter - Improve Emails with AI | SandBox",
        "description": "Rewrite emails for tone, clarity, and professionalism with SandBox's AI Email Rewriter.",
    },
    "/blog-outline-generator": {
        "title": "Blog Outline Generator - Plan Blog Posts with AI | SandBox",
        "description": "Generate structured blog outlines, headings, and content direction for articles with SandBox.",
    },
    "/pro_cons_gen": {
        "title": "Pros and Cons Generator - Compare Decisions | SandBox",
        "description": "Generate balanced pros and cons for topics, ideas, and decisions with SandBox's AI comparison tool.",
    },
    "/quiz-generator": {
        "title": "Quiz Generator - Create Quizzes with AI | SandBox",
        "description": "Create quizzes from topics or documents with SandBox's AI Quiz Generator for learning and review.",
    },
    "/flashcard-generator": {
        "title": "Flashcard Generator - Make Study Flashcards | SandBox",
        "description": "Generate study flashcards from learning material with SandBox's AI Flashcard Generator.",
    },
    "/youtube-summarizer": {
        "title": "YouTube Summarizer - Summarize Videos | SandBox",
        "description": "Summarize YouTube videos into concise notes and key takeaways with SandBox's AI YouTube Summarizer.",
    },
    "/regex-gen": {
        "title": "Regex Generator - Build Regular Expressions | SandBox",
        "description": "Generate regex patterns from plain English and test pattern ideas faster with SandBox.",
    },
    "/decision-maker": {
        "title": "Decision Maker - Compare Options with AI | SandBox",
        "description": "Compare choices, risks, pros, cons, and recommendations with SandBox's AI Decision Maker.",
    },
    "/commit-gen": {
        "title": "Commit Message Generator - Write Git Commits | SandBox",
        "description": "Generate clear Git commit messages from code changes and development context with SandBox.",
    },
    "/error": {
        "title": "Error Explainer - Debug Error Messages | SandBox",
        "description": "Paste error messages and get simple explanations, likely causes, and next debugging steps with SandBox.",
    },
    "/yaml": {
        "title": "YAML Generator - Create Kubernetes YAML | SandBox",
        "description": "Generate Kubernetes YAML for deployments, services, config maps, and related resources with SandBox.",
    },
    "/code": {
        "title": "Code Reviewer - Review Code with AI | SandBox",
        "description": "Review code for bugs, clarity, and improvements with SandBox's AI Code Reviewer.",
    },
    "/docker": {
        "title": "Dockerfile Generator - Create Docker Configs | SandBox",
        "description": "Generate Dockerfiles and container setup guidance from project context with SandBox.",
    },
    "/item": {
        "title": "Item Extractor - Extract Structured Items | SandBox",
        "description": "Extract structured items from uploaded content and turn unstructured inputs into useful data with SandBox.",
    },
    "/brainstorm-generator": {
        "title": "Brainstorm Generator - Generate Ideas with AI | SandBox",
        "description": "Brainstorm ideas, angles, and creative directions for projects, writing, and planning with SandBox.",
    },
}


PRIVATE_PAGES = {
    "/bookmarks_page": "Bookmarks",
    "/forgot-password": "Forgot Password",
    "/history": "History",
    "/login": "Login",
    "/profile": "Profile",
    "/reset-password": "Reset Password",
    "/settings": "Settings",
    "/signup": "Sign Up",
    "/user": "User Panel",
}


def add_page_seo(path: str) -> None:
    metadata = PUBLIC_PAGES[path]
    url = absolute_url(path)
    image = absolute_url(DEFAULT_IMAGE_PATH)

    head_tags = [
        _tag(
            "meta",
            {
                "name": "description",
                "content": metadata["description"],
            },
        ),
        _tag(
            "meta",
            {
                "name": "robots",
                "content": "index,follow",
            },
        ),
        _tag(
            "link",
            {
                "rel": "canonical",
                "href": url,
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:type",
                "content": "website",
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:title",
                "content": metadata["title"],
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:description",
                "content": metadata["description"],
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:url",
                "content": url,
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:site_name",
                "content": SITE_NAME,
            },
        ),
        _tag(
            "meta",
            {
                "property": "og:image",
                "content": image,
            },
        ),
        _tag(
            "meta",
            {
                "name": "twitter:card",
                "content": "summary_large_image",
            },
        ),
        _tag(
            "meta",
            {
                "name": "twitter:title",
                "content": metadata["title"],
            },
        ),
        _tag(
            "meta",
            {
                "name": "twitter:description",
                "content": metadata["description"],
            },
        ),
        _tag(
            "meta",
            {
                "name": "twitter:image",
                "content": image,
            },
        ),
    ]

    if path == "/":
        structured_data = [
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": absolute_url("/"),
            },
            {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": SITE_NAME,
                "url": absolute_url("/"),
                "applicationCategory": "ProductivityApplication",
                "operatingSystem": "Web",
                "description": PUBLIC_PAGES["/"]["description"],
            },
        ]

        head_tags.append(
            f'<script type="application/ld+json">'
            f'{json.dumps(structured_data, separators=(",", ":"))}'
            f"</script>"
        )

    ui.add_head_html("\n".join(head_tags))


def add_private_seo(path: str) -> None:
    ui.add_head_html(
        "\n".join(
            [
                _tag(
                    "meta",
                    {
                        "name": "robots",
                        "content": "noindex,nofollow",
                    },
                ),
                _tag(
                    "link",
                    {
                        "rel": "canonical",
                        "href": absolute_url(path),
                    },
                ),
            ]
        )
    )


def robots_txt() -> str:
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {absolute_url('/sitemap.xml')}",
            "",
        ]
    )


def sitemap_xml() -> str:
    urls = []

    for path in PUBLIC_PAGES:
        urls.append(
            "  <url>\n"
            f"    <loc>{html.escape(absolute_url(path))}</loc>\n"
            "  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
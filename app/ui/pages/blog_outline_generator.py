from datetime import datetime
from pathlib import Path

from nicegui import ui
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/blog-outline-generator", title=PUBLIC_PAGES["/blog-outline-generator"]["title"])
def blog_outline_generator_page():
    add_page_seo("/blog-outline-generator")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/blog_outline_generator.css">
    <script src="/assets/js/blog_outline_generator.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "blog_outline_generator.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

from datetime import datetime
from pathlib import Path

from nicegui import ui
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets


@ui.page("/blog-outline-generator", title=PUBLIC_PAGES["/blog-outline-generator"]["title"])
def blog_outline_generator_page():
    add_page_seo("/blog-outline-generator")

    add_shared_assets(
        extra_css=["/assets/css/blog_outline_generator.css"],
        extra_js=["/assets/js/blog_outline_generator.js"],
    )

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

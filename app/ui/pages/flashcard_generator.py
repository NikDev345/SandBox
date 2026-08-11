from datetime import datetime
from pathlib import Path
from app.ui.shared import add_shared_assets
from nicegui import ui
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/flashcard-generator", title=PUBLIC_PAGES["/flashcard-generator"]["title"])
def flashcard_generator_page():
    add_page_seo("/flashcard-generator")

    add_shared_assets(
        extra_css=["/assets/css/flashcard_generator.css"],
        extra_js=["/assets/js/flashcard_generator.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "flashcard_generator.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

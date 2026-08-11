from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/quiz-generator", title=PUBLIC_PAGES["/quiz-generator"]["title"])
def quiz_generator_page():
    add_page_seo("/quiz-generator")

    add_shared_assets(
            extra_css=["/assets/css/quiz_generator.css"],
            extra_js=["/assets/js/quiz_generator.js"],
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "quiz_generator.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

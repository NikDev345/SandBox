from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets


@ui.page("/brainstorm-generator", title=PUBLIC_PAGES["/brainstorm-generator"]["title"])
def brainstorm_generator_page():
    add_page_seo("/brainstorm-generator")

    add_shared_assets(
        extra_css=["/assets/css/brainstorm_generator.css"],
        extra_js=["/assets/js/brainstorm_generator.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "brainstorm_generator.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/table_extractor", title=PUBLIC_PAGES["/table_extractor"]["title"])
def table_extractor_page():
    add_page_seo("/table_extractor")

    add_shared_assets(
        extra_css=["/assets/css/table_extractor.css"],
        extra_js=["/assets/js/table_extractor.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "table_extractor.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

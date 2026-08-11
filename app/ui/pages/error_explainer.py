from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/error", title=PUBLIC_PAGES["/error"]["title"])
def commit_gen():
    add_page_seo("/error")

    add_shared_assets(
        extra_css=["/assets/css/error.css"],
        extra_js=["/assets/js/error.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "error.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

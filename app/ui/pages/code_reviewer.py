from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/code", title=PUBLIC_PAGES["/code"]["title"])
def code_reviewer():
    add_page_seo("/code")

    add_shared_assets(
        extra_css=["/assets/css/code_reviewer.css"],
        extra_js=["/assets/js/code_reviewer.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "code_reviewer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

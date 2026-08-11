from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/json-fixer", title=PUBLIC_PAGES["/json-fixer"]["title"])
def json_fixer_page():
    add_page_seo("/json-fixer")

    add_shared_assets(
            extra_css=["/assets/css/json_fixer.css"],
            extra_js=["/assets/js/json_fixer.js"],
            tool_page=True,
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "json_fixer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

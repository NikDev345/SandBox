from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/pro_cons_gen", title=PUBLIC_PAGES["/pro_cons_gen"]["title"])
def json_fixer_page():
    add_page_seo("/pro_cons_gen")

    add_shared_assets(
            extra_css=["/assets/css/pro_cons.css"],
            extra_js=["/assets/js/pro_cons.js"],
            tool_page=True,
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "pro_cons.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

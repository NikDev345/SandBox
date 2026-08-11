from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets


@ui.page("/sql_gen", title=PUBLIC_PAGES["/sql_gen"]["title"])
def sql_gen():
    add_page_seo("/sql_gen")

    add_shared_assets(
        extra_css=["/assets/css/sql_gen.css"],
        extra_js=["/assets/js/sql_gen.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "sql_gen.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

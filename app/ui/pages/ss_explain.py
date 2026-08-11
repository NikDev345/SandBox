from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/ss_explain", title=PUBLIC_PAGES["/ss_explain"]["title"])
def ss_explainer():
    add_page_seo("/ss_explain")

    add_shared_assets(
        extra_css=["/assets/css/ss_explain.css"],
        extra_js=["/assets/js/ss_explain.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "ss_explain.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

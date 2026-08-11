from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/decision-maker", title=PUBLIC_PAGES["/decision-maker"]["title"])
def decision_maker_page():
    add_page_seo("/decision-maker")

    add_shared_assets(
        extra_css=["/assets/css/decision_maker.css"],
        extra_js=["/assets/js/decision_maker.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "decision_maker.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

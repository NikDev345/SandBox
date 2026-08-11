from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets


@ui.page("/chart-explainer", title=PUBLIC_PAGES["/chart-explainer"]["title"])
def chart_explainer_page():
    add_page_seo("/chart-explainer")

    add_shared_assets(
        extra_css=["/assets/css/chart_explainer.css"],
        extra_js=["/assets/js/chart_explainer.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "chart_explainer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

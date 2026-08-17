from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets


@ui.page("/history", title=f"{PRIVATE_PAGES['/history']} - SandBox")
def history_page():
    add_private_seo("/history")

    add_shared_assets(
                extra_css=["/assets/css/history.css",
                           "/assets/css/tool-back-button.css"],
                extra_js=["/assets/js/history.js",
                          "/assets/js/tool-back-button.js"],
            )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "history.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

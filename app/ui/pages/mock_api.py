from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/mock_api", title=PUBLIC_PAGES["/mock_api"]["title"])
def mock_api():
    add_page_seo("/mock_api")

    add_shared_assets(
            extra_css=["/assets/css/mock_api.css"],
            extra_js=["/assets/js/api.js",
                      "/assets/js/mock_api.js",
                      "/assets/js/ui.js"],
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "mock_api.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

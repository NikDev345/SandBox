from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/eli5", title=PUBLIC_PAGES["/eli5"]["title"])
def eli5_page():
    add_page_seo("/eli5")

    add_shared_assets(
        extra_css=["/assets/css/eli5.css"],
        extra_js=["/assets/js/eli5.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "eli5.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

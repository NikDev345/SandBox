from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/item", title=PUBLIC_PAGES["/item"]["title"])
def item_extract():
    add_page_seo("/item")

    add_shared_assets(
        extra_css=["/assets/css/item.css"],
        extra_js=["/assets/js/item.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "item.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

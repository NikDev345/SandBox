from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/image-text-extractor", title=PUBLIC_PAGES["/image-text-extractor"]["title"])
def image_text_extractor_page():
    add_page_seo("/image-text-extractor")

    add_shared_assets(
        extra_css=["/assets/css/image_text_extractor.css"],
        extra_js=["/assets/js/image_text_extractor.js"],
        tool_page=True,
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "image_text_extractor.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

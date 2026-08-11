from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/text-summarizer", title=PUBLIC_PAGES["/text-summarizer"]["title"])
def text_summarizer_page():
    add_page_seo("/text-summarizer")

    add_shared_assets(
            extra_css=["/assets/css/text_summarizer.css"],
            extra_js=["/assets/js/text_summarizer.js"],
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "text_summarizer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

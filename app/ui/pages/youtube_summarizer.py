from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/youtube-summarizer", title=PUBLIC_PAGES["/youtube-summarizer"]["title"])
def youtube_summarizer_page():
    add_page_seo("/youtube-summarizer")

    add_shared_assets(
                extra_css=["/assets/css/youtube_summarizer.css"],
                extra_js=["/assets/js/youtube_summarizer.js"],
            )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "youtube_summarizer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

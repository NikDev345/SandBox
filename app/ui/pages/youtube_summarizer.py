from nicegui import ui
from datetime import datetime
from pathlib import Path


@ui.page("/youtube-summarizer")
def youtube_summarizer_page():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/youtube_summarizer.css">
    <script src="/assets/js/youtube_summarizer.js" defer></script>
    """)

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
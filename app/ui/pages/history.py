from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PRIVATE_PAGES, add_private_seo


@ui.page("/history", title=f"{PRIVATE_PAGES['/history']} - SandBox")
def history_page():
    add_private_seo("/history")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/history.css">
    <script src="/assets/js/history.js" defer></script>
    """)

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

from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/notes_cleaner", title=PUBLIC_PAGES["/notes_cleaner"]["title"])
def ss_explainer():
    add_page_seo("/notes_cleaner")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/notes_cleaner.css">
    <script src="/assets/js/notes_cleaner.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "notes_cleaner.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

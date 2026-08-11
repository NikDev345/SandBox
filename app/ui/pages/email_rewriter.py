from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/email-rewriter", title=PUBLIC_PAGES["/email-rewriter"]["title"])
def email_rewriter_page():
    add_page_seo("/email-rewriter")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/email_rewriter.css">
    <script src="/assets/js/email_rewriter.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "email_rewriter.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

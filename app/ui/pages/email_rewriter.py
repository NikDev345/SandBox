from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/email-rewriter", title=PUBLIC_PAGES["/email-rewriter"]["title"])
def email_rewriter_page():
    add_page_seo("/email-rewriter")

    add_shared_assets(
        extra_css=["/assets/css/email_rewriter.css"],
        extra_js=["/assets/js/email_rewriter.js"],
        tool_page=True,
    )

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

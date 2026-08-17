from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/notes_cleaner", title=PUBLIC_PAGES["/notes_cleaner"]["title"])
def ss_explainer():
    add_page_seo("/notes_cleaner")

    add_shared_assets(
        extra_css=["/assets/css/notes_cleaner.css",
                   "/assets/css/tool-back-button.css"],
        extra_js=["/assets/js/notes_cleaner.js",
                  "/assets/js/tool-back-button.js"],
        tool_page=True,
    )

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

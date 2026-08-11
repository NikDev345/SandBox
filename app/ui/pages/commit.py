from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/commit-gen", title=PUBLIC_PAGES["/commit-gen"]["title"])
def commit_gen():
    add_page_seo("/commit-gen")

    add_shared_assets(
        extra_css=["/assets/css/commit.css"],
        extra_js=["/assets/js/commit.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "commit.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

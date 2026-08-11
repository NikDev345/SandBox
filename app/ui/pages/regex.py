from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/regex-gen", title=PUBLIC_PAGES["/regex-gen"]["title"])
def regex_gen():
    add_page_seo("/regex-gen")

    add_shared_assets(
                extra_css=["/assets/css/regex.css"],
                extra_js=["/assets/js/regex.js"],
            )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "regex.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

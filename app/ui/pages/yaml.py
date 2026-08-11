from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets


@ui.page("/yaml", title=PUBLIC_PAGES["/yaml"]["title"])
def yaml_gen():
    add_page_seo("/yaml")

    add_shared_assets(
            extra_css=["/assets/css/yaml.css"],
            extra_js=["/assets/js/yaml.js"],
            tool_page=True,
        )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "yaml.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

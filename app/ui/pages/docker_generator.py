from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/docker", title=PUBLIC_PAGES["/docker"]["title"])
def docker_gen():
    add_page_seo("/docker")

    add_shared_assets(
        extra_css=["/assets/css/docker_gen.css"],
        extra_js=["/assets/js/docker_gen.js"],
    )

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "docker_gen.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

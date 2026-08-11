from nicegui import ui
from datetime import datetime
from pathlib import Path
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/docker", title=PUBLIC_PAGES["/docker"]["title"])
def docker_gen():
    add_page_seo("/docker")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/docker_gen.css">
    <script src="/assets/js/docker_gen.js" defer></script>
    """)

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

from nicegui import ui
from datetime import datetime
from pathlib import Path


@ui.page("/eli5")
def eli5_page():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/eli5.css">
    <script src="/assets/js/eli5.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "eli5.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)
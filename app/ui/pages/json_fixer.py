from nicegui import ui
from datetime import datetime
from pathlib import Path


@ui.page("/json-fixer")
def json_fixer_page():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/json_fixer.css">
    <script src="/assets/js/json_fixer.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "json_fixer.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)
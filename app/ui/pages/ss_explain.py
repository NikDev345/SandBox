from nicegui import ui
from datetime import datetime
from pathlib import Path


@ui.page("/ss_explain")
def ss_explainer():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/ss_explain.css">
    <script src="/assets/js/ss_explain.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "ss_explain.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)
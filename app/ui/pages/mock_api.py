from nicegui import ui
from datetime import datetime
from pathlib import Path


@ui.page("/mock_api")
def mock_api():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/mock_api.css">
    <script src="/assets/js/mock_api/api.js" defer></script>
    <script src="/assets/js/mock_api/mock_api.js" defer></script>
    <script src="/assets/js/mock_api/ui.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "mock_api.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)
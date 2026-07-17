from datetime import datetime
from pathlib import Path

from nicegui import ui


@ui.page("/flashcard-generator")
def flashcard_generator_page():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/flashcard_generator.css">
    <script src="/assets/js/flashcard_generator.js" defer></script>
    """)

    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "flashcard_generator.html"
    )

    html = template_path.read_text(encoding="utf-8")

    html = html.replace(
        "{{TIMESTAMP}}",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    ui.add_body_html(html)

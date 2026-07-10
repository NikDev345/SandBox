from pathlib import Path
from nicegui import ui

BASE = Path(__file__).resolve().parents[2]

@ui.page("/tools/code-reviewer")
def code_reviewer():

    template = BASE / "ui" / "templates" / "code_reviewer.html"

    ui.html(template.read_text(encoding="utf-8"))
    for css in (
        "tokens.css",
        "animations.css",
        "dashboard.css",
        "code_reviewer.css",
    ):
        ui.add_head_html(
            f'<link rel="stylesheet" href="/assets/css/{css}">'
        )
        
    ui.add_head_html("""
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.39.0/ace.js"></script>
    """)
    
    ui.add_body_html("""
    <script src="/assets/js/code_reviewer.js"></script>
    """)
    
    
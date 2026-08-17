# app/ui/shared.py
import json
from nicegui import ui
from app.utils.tools_registry import TOOLS

def add_shared_assets(
    extra_css: list[str] = [],
    extra_js: list[str] = [],
    auth_page: bool = False,
    tool_page: bool = False,
):
    # Only tokens and animations load everywhere
    base_css = [
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
        "/assets/css/tokens.css",
        "/assets/css/animations.css",
        "/assets/css/buttons.css",
        "/assets/css/layout.css",
    ]

    # Dashboard and settings only on dashboard/settings pages
    if not auth_page and not tool_page:
        base_css += [
            "/assets/css/dashboard.css",
            "/assets/css/settings.css",
        ]
        
    base_js = [
        "/assets/js/transitions.js",
    ]
    if tool_page:
        base_css += [
            "/assets/css/sidebar.css",
        ]

        base_js += [
            "/assets/js/tool_switcher.js",
        ]


    css_tags = "\n".join(
        f'<link rel="stylesheet" href="{href}">'
        for href in base_css + extra_css
    )

    js_tags = "\n".join(
        f'<script src="{src}" defer></script>'
        for src in base_js + extra_js
    )

    ui.add_head_html(css_tags + "\n" + js_tags)
    ui.add_head_html(f"""
        <script>
            window.TOOLS = {json.dumps(TOOLS)};
        </script>
        """)
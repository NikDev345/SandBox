# app/ui/shared.py

from nicegui import ui

def add_shared_assets(extra_css: list[str] = [], extra_js: list[str] = [], auth_page: bool = False):

    base_css = [
        "/assets/css/tokens.css",
        "/assets/css/animations.css",
    ]

    if not auth_page:
        base_css += [
            "/assets/css/dashboard.css",
            "/assets/css/settings.css",
        ]

    base_js = [
        "/assets/js/transitions.js",
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
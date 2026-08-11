# app/ui/shared.py

def add_shared_assets(extra_css: list[str] = [], extra_js: list[str] = []):
    from nicegui import ui

    base_css = [
        "/assets/css/tokens.css",
        "/assets/css/animations.css",
        "/assets/css/dashboard.css",
        "/assets/css/settings.css",
    ]

    base_js = [
        "/assets/js/transitions.js",  # ← shared transition on every page
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
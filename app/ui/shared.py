from nicegui import ui


def add_shared_assets(
    extra_css: list[str] = [],
    extra_js: list[str] = [],
    auth_page: bool = False,
    tool_page: bool = False,
):

    base_css = [
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
        "/assets/css/tokens.css",
        "/assets/css/animations.css",
        "/assets/css/buttons.css",
        "/assets/css/layout.css",
    ]

    # Tool pages
    if tool_page or auth_page:
        base_css.append(
            "/assets/css/tool-back-button.css"
        )

    # Dashboard and settings only on dashboard/settings pages
    if not auth_page and not tool_page:
        base_css += [
            "/assets/css/dashboard.css",
            "/assets/css/settings.css",
        ]

    base_js = [
        "/assets/js/transitions.js",
    ]

    # Tool pages
    if tool_page:
        base_js.append(
            "/assets/js/tool-back-button.js"
        )

    css_tags = "\n".join(
        f'<link rel="stylesheet" href="{href}">'
        for href in base_css + extra_css
    )

    js_tags = "\n".join(
        f'<script src="{src}" defer></script>'
        for src in base_js + extra_js
    )

    ui.add_head_html(
        css_tags + "\n" + js_tags
    )
from nicegui import ui
from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page("/", title=PUBLIC_PAGES["/"]["title"])
def dashboard():
    add_page_seo("/")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    <link rel="stylesheet" href="/assets/css/layout.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/appearance.js"></script>
    <script src="/assets/js/dashboard.js"></script>
    <script src="/assets/js/settings.js"></script>
    """)

    with open(
        "app/ui/templates/dashboard.html",
        encoding="utf-8",
    ) as f:
        ui.html(f.read())

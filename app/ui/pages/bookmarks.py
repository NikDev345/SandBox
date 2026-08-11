from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo

@ui.page("/bookmarks_page", title=f"{PRIVATE_PAGES['/bookmarks_page']} - SandBox")
def bookmarks():
    add_private_seo("/bookmarks_page")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="/assets/css/bookmarks.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/appearance.js"></script>
    <script src="/assets/js/bookmarks.js"></script>
    """)

    with open(
        "app/ui/templates/bookmarks.html",
        encoding="utf-8"
    ) as f:

        ui.html(
            f.read()
        )

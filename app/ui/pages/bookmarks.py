from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets

@ui.page("/bookmarks_page", title=f"{PRIVATE_PAGES['/bookmarks_page']} - SandBox")
def bookmarks():
    add_private_seo("/bookmarks_page")

    add_shared_assets(
        extra_css=["/assets/css/bookmarks.css"],
        extra_js=["/assets/js/bookmarks.js"],
    )

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

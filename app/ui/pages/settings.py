from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets

@ui.page("/settings", title=f"{PRIVATE_PAGES['/settings']} - SandBox")
def settings():
    add_private_seo("/settings")

    add_shared_assets(
        extra_css=[
            "/assets/css/appearance.css",
            "/assets/css/layout.css",
        ],
        extra_js=[
            "/assets/js/appearance.js",
            "/assets/js/settings.js",
        ],
    )

    with open(
        "app/ui/templates/settings.html",
        encoding="utf-8"
    ) as f:

        ui.html(
            f.read()
        )

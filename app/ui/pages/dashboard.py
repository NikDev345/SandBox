from nicegui import ui
from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.shared import add_shared_assets

@ui.page("/", title=PUBLIC_PAGES["/"]["title"])
def dashboard():
    add_page_seo("/")

    add_shared_assets(
        extra_css=["/assets/css/layout.css"],
        extra_js=[
            "/assets/js/appearance.js",
            "/assets/js/dashboard.js",
            "/assets/js/settings.js",
        ],
    )

    with open(
        "app/ui/templates/dashboard.html",
        encoding="utf-8",
    ) as f:
        ui.html(f.read())

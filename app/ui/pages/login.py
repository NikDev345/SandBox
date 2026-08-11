from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets

@ui.page('/login', title=f"{PRIVATE_PAGES['/login']} - SandBox")
def login_page():
    add_private_seo("/login")

    add_shared_assets(
        extra_css=["/assets/css/auth.css"],
        extra_js=[
            "/assets/js/appearance.js",
            "/assets/js/login.js",
        ],
        auth_page=True,
    )

    with open(
        "app/ui/templates/login.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())


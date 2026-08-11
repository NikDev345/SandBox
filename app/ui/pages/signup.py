from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets

@ui.page('/signup', title=f"{PRIVATE_PAGES['/signup']} - SandBox")
def signup_page():
    add_private_seo("/signup")

    add_shared_assets(
        extra_css=["/assets/css/auth.css"],
        extra_js=[
            "/assets/js/appearance.js",
            "/assets/js/signup.js",
        ],
        auth_page=True
    )

    with open(
        "app/ui/templates/signup.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())

from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo
from app.ui.shared import add_shared_assets

@ui.page("/reset-password", title=f"{PRIVATE_PAGES['/reset-password']} - SandBox")
def reset_password():
    add_private_seo("/reset-password")

    add_shared_assets(
        extra_css=["/assets/css/auth.css"],
        extra_js=["/assets/js/reset_password.js"],
        auth_page=True,
    )

    with open(
        "app/ui/templates/reset_password.html",
        encoding="utf-8"
    ) as f:
        ui.html(f.read())
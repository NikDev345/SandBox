from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo

@ui.page('/login', title=f"{PRIVATE_PAGES['/login']} - SandBox")
def login_page():
    add_private_seo("/login")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/auth.css">
    """)

    with open(
        "app/ui/templates/login.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())

    ui.add_body_html("""
        <script src="/assets/js/appearance.js"></script>
        <script src="/assets/js/login.js"></script>
    """)

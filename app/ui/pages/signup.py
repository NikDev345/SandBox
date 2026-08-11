from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo


@ui.page('/signup', title=f"{PRIVATE_PAGES['/signup']} - SandBox")
def signup_page():
    add_private_seo("/signup")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/auth.css">
    """)

    ui.add_body_html("""
        <script src="/assets/js/appearance.js"></script>
        <script src="/assets/js/signup.js"></script>
    """)

    with open(
        "app/ui/templates/signup.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())

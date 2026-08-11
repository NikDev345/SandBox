from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo

with open(
    "app/ui/templates/reset_password.html",
    "r",
    encoding="utf-8"
) as f:
    html = f.read()


@ui.page("/reset-password", title=f"{PRIVATE_PAGES['/reset-password']} - SandBox")
def reset_password():
    add_private_seo("/reset-password")

    ui.add_head_html("""
        <link rel="stylesheet" href="/assets/css/auth.css">
        <script src="/assets/js/reset_password.js" defer></script>
    """)

    ui.html(html)

from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo

with open("app/ui/templates/forgot_password.html", "r", encoding="utf-8") as f:
    html = f.read()


@ui.page("/forgot-password", title=f"{PRIVATE_PAGES['/forgot-password']} - SandBox")
def forgot_password():
    add_private_seo("/forgot-password")

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/auth.css">
    <script src="/assets/js/forgot_password.js" defer></script>
    """)

    ui.html(html)

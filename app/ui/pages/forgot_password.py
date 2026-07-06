from nicegui import ui

with open("app/ui/templates/forgot_password.html", "r", encoding="utf-8") as f:
    html = f.read()


@ui.page("/forgot-password")
def forgot_password():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/auth.css">
    <script src="/assets/js/forgot_password.js" defer></script>
    """)

    ui.html(html)
from nicegui import ui

with open(
    "app/ui/templates/reset_password.html",
    "r",
    encoding="utf-8"
) as f:
    html = f.read()


@ui.page("/reset-password")
def reset_password():

    ui.add_head_html("""
        <link rel="stylesheet" href="/assets/css/auth.css">
        <script src="/assets/js/reset_password.js" defer></script>
    """)

    ui.html(html)
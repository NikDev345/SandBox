from nicegui import ui

@ui.page('/login')
def login_page():

    ui.add_head_html("""
    <link rel="stylesheet"
    href="/assets/css/auth.css">
    """)

    with open(
        "app/ui/templates/login.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())

    ui.add_body_html(
        '<script src="/assets/js/login.js"></script>'
    )
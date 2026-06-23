from nicegui import ui


@ui.page('/signup')
def signup_page():

    ui.add_head_html("""
    <link rel="stylesheet"
    href="/assets/css/auth.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/signup.js"></script>
    """)

    with open(
        "app/ui/templates/signup.html",
        encoding="utf-8"
    ) as f:

        ui.html(f.read())
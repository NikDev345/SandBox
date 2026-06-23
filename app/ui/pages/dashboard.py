from nicegui import ui


@ui.page('/dashboard')
def dashboard():

    ui.add_head_html("""
    <link rel="stylesheet"
    href="/assets/css/dashboard.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/dashboard.js"></script>
    """)

    with open(
        'app/ui/templates/dashboard.html',
        encoding='utf-8'
    ) as f:

        ui.html(
            f.read()
        )

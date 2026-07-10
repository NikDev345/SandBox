from nicegui import ui


@ui.page("/")
def dashboard():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="/assets/css/settings.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/appearance.js"></script>
    <script src="/assets/js/dashboard.js"></script>
    <script src="/assets/js/settings.js"></script>
    """)

    with open(
        "app/ui/templates/dashboard.html",
        encoding="utf-8",
    ) as f:
        ui.html(f.read())
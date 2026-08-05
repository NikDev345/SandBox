from nicegui import ui

@ui.page("/bookmarks_page")
def bookmarks():

    ui.add_head_html("""
    <link rel="stylesheet" href="/assets/css/tokens.css">
    <link rel="stylesheet" href="/assets/css/animations.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="/assets/css/bookmarks.css">
    """)

    ui.add_body_html("""
    <script src="/assets/js/appearance.js"></script>
    <script src="/assets/js/bookmarks.js"></script>
    """)

    with open(
        "app/ui/templates/bookmarks.html",
        encoding="utf-8"
    ) as f:

        ui.html(
            f.read()
        )
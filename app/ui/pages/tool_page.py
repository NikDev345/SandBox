from nicegui import ui

@ui.page("/tools/{slug}")
def tool_page(slug: str):

    slug = slug.upper()

    if slug == "CODE-REVIEWER":

        ui.add_head_html("""
        <link rel="stylesheet" href="/assets/css/tokens.css">
        <link rel="stylesheet" href="/assets/css/animations.css">
        <link rel="stylesheet" href="/assets/css/dashboard.css">
        <link rel="stylesheet" href="/assets/css/code_reviewer.css">

        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.js"></script>
        """)

        ui.add_body_html("""
        <script src="/assets/js/code_reviewer.js"></script>
        """)

        with open(
            "app/ui/templates/code_reviewer.html",
            encoding="utf-8"
        ) as f:
            ui.html(f.read())

        return

    with open(
        "app/ui/templates/tool_page.html",
        encoding="utf-8"
    ) as f:

        html = f.read()

        html = html.replace(
            "{{TOOL_NAME}}",
            slug.replace("-", " ").title()
        )

        ui.html(html)
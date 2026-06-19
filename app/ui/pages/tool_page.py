from nicegui import ui


@ui.page('/tools/{slug}')
def tool_page(slug: str):

    with open(
        'app/ui/templates/tool_page.html',
        encoding='utf-8'
    ) as f:

        html = f.read()

        html = html.replace(
            '{{TOOL_NAME}}',
            slug.replace('-', ' ').title()
        )

        ui.html(html)
# app/ui/layout.py

from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer


def page_layout():

    # Head elements must be created inside the page context.
    ui.add_head_html(
        """
        <script type="module" src="/assets/js/appearance.js"></script>
        """
    )

    navbar()

    ui.separator()

    footer()
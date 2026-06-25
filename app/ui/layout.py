# app/ui/layout.py

from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer

ui.add_head_html(
    """
    <script type="module" src="/assets/js/appearance.js"></script>
    """
)

def page_layout():

    navbar()

    ui.separator()

    footer()
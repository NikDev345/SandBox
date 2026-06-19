# app/ui/layout.py

from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer


def page_layout():

    navbar()

    ui.separator()

    footer()
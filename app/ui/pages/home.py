# app/ui/pages/home.py

from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer
from app.ui.components.tool_card import tool_card


@ui.page('/home')
def home_page():

    navbar()

    with ui.column().classes(
        'w-full items-center p-10'
    ):

        ui.label(
            'AI TOOLBOX'
        ).classes(
            'text-5xl font-bold text-cyan-400'
        )

        ui.label(
            'One Platform. Many Tools.'
        ).classes(
            'text-xl'
        )

        with ui.row():

            ui.button('Browse Tools')
            ui.button('Login')

        ui.separator()

        ui.label(
            'Popular Tools'
        ).classes(
            'text-2xl font-bold'
        )

        with ui.row():

            tool_card(
                'SQL Generator',
                'Generate SQL from plain English.'
            )

            tool_card(
                'Regex Generator',
                'Generate regex patterns instantly.'
            )

            tool_card(
                'JSON Fixer',
                'Fix invalid JSON automatically.'
            )

    footer()
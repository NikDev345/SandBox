# app/ui/components/navbar.py

from nicegui import ui


def navbar():
    with ui.header().classes(
        'items-center justify-between px-6 bg-slate-900 text-white'
    ):
        ui.label('AI Toolbox').classes(
            'text-xl font-bold text-cyan-400'
        )

        with ui.row():
            ui.button('Home')
            ui.button('Tools')
            ui.button('Login')
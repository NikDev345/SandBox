# app/ui/components/tool_card.py

from nicegui import ui


def tool_card(title: str, description: str):

    with ui.card().classes(
        'w-80 bg-slate-800 text-white'
    ):

        ui.label(title).classes(
            'text-lg font-bold text-cyan-400'
        )

        ui.label(description)

        ui.button(
            'Open Tool'
        ).classes('w-full')
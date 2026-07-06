from nicegui import ui


def user_header(title: str, subtitle: str):

    with ui.column().classes("w-full mb-8"):

        ui.label(title).classes(
            "text-4xl font-bold text-white"
        )

        ui.label(subtitle).classes(
            "text-slate-400 text-base"
        )
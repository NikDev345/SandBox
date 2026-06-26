from nicegui import ui


def settings_card(title: str, description: str):

    with ui.card().classes(
        """
        w-full
        rounded-2xl
        bg-slate-900
        border
        border-slate-800
        shadow-lg
        p-6
        """
    ):

        ui.label(title).classes(
            "text-xl font-semibold text-white"
        )

        ui.label(description).classes(
            "text-slate-400 text-sm mb-4"
        )

        return ui.column().classes(
            "w-full gap-4"
        )
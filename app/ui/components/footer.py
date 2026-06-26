# app/ui/components/footer.py

from nicegui import ui


def footer():
    with ui.footer().classes(
        'bg-slate-900 text-white justify-center'
    ):
        ui.label(
            '© AI SandBox 2026'
        ).classes('text-sm')
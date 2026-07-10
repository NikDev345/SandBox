from nicegui import ui

@ui.page("/test")
def test():
    ui.label("Hello")
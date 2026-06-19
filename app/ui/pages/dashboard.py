from nicegui import ui


@ui.page('/')
def dashboard():

    with open(
        'app/ui/templates/dashboard.html',
        encoding='utf-8'
    ) as f:

        ui.html(
            f.read()
        )
from nicegui import ui


class Workspace:

    @staticmethod
    def create():

        with ui.column().classes(
            "layout-page"
        ):

            with ui.column().classes(
                "layout-tool"
            ) as workspace:

                return workspace
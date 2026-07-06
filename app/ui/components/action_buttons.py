from nicegui import ui


class ActionButtons:

    @staticmethod
    def create():

        with ui.row().classes(
            "action-bar"
        ):

            copy_button = (
                ui.button(
                    "Copy",
                    icon="content_copy",
                )
                .classes("btn-secondary")
            )

            download_button = (
                ui.button(
                    "Download",
                    icon="download",
                )
                .classes("btn-secondary")
            )

            history_button = (
                ui.button(
                    "History",
                    icon="history",
                )
                .classes("btn-secondary")
            )

            clear_button = (
                ui.button(
                    "Clear",
                    icon="delete_outline",
                )
                .classes("btn-danger")
            )

        return (
            copy_button,
            download_button,
            history_button,
            clear_button,
        )
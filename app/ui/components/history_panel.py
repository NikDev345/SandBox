from nicegui import ui


class HistoryPanel:

    @staticmethod
    def create():

        with ui.card().classes(
            "glass-card"
        ):

            with ui.row().classes(
                "glass-card-header"
            ):

                ui.icon("history")

                ui.label(
                    "Recent History"
                ).classes(
                    "text-lg text-weight-bold"
                )

            history = ui.column().classes(
                "gap-y-3"
            )

            with history:

                ui.label(
                    "No summaries yet."
                ).classes(
                    "text-sm text-secondary"
                )

        def add_item(
            title: str,
            created_at: str,
        ):

            with history:

                with ui.card().classes(
                    "card card-info"
                ):

                    ui.label(title).classes(
                        "info-title"
                    )

                    ui.label(created_at).classes(
                        "info-meta"
                    )

        return {
            "container": history,
            "add_item": add_item,
        }
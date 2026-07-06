from nicegui import ui


class ToolHeader:

    @staticmethod
    def create(
        title: str,
        description: str,
        icon: str = "smart_toy",
        model: str = "Gemini 2.5 Flash",
        category: str = "AI TOOL",
    ):

        with ui.column().classes("tool-header"):

            # -------------------------------
            # Top Row
            # -------------------------------

            with ui.row().classes("tool-header-top"):

                with ui.row().classes("tool-title-group"):

                    ui.icon(icon).classes("tool-icon")

                    with ui.column().classes("tool-title-wrapper"):

                        ui.label(title).classes("tool-title")

                        ui.label(description).classes(
                            "tool-description"
                        )

                with ui.row().classes("tool-badge-group"):

                    ui.label(category).classes(
                        "tool-badge"
                    )

                    ui.label(model).classes(
                        "tool-badge tool-model-badge"
                    )

            ui.separator().classes("tool-divider")
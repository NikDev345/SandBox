from nicegui import ui


class ToolFooter:

    @staticmethod
    def create(
        model: str = "Gemini 2.5 Flash",
        max_chars: str = "50,000 Characters",
    ):

        with ui.row().classes(
            "layout-tool-footer"
        ):

            with ui.row().classes(
                "gap-x-3"
            ):

                ui.label(
                    f"⚡ {model}"
                ).classes(
                    "glass-badge glass-badge-primary"
                )

                ui.label(
                    max_chars
                ).classes(
                    "glass-badge"
                )

            ui.label(
                "AI responses may contain mistakes."
            ).classes(
                "text-sm text-secondary"
            )
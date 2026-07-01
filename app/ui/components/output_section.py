from nicegui import ui


class OutputSection:

    @staticmethod
    def create(
        label: str = "Generated Summary",
        placeholder: str = "Your AI generated response will appear here...",
    ):

        with ui.column().classes("w-full gap-3"):

            ui.label(label).classes(
                "section-title"
            )

            with ui.card().classes(
                "glass-card output-card w-full"
            ):

                output = (
                    ui.textarea(
                        placeholder=placeholder,
                    )
                    .props("outlined readonly autogrow")
                    .classes("form-textarea w-full")
                )

                output.style(
                    "min-height:320px;"
                )

                ui.separator()

                with ui.row().classes(
                    "w-full justify-between items-center"
                ):

                    word_count = ui.label(
                        "0 Words"
                    ).classes(
                        "output-stat"
                    )

                    character_count = ui.label(
                        "0 Characters"
                    ).classes(
                        "output-stat"
                    )

                    reading_time = ui.label(
                        "0 Min Read"
                    ).classes(
                        "output-stat"
                    )

        return (
            output,
            word_count,
            character_count,
            reading_time,
        )
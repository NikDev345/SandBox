from nicegui import ui


class OptionBar:

    @staticmethod
    def create(
        options: list,
        value: str,
        label: str = "Summary Length",
        button_text: str = "Generate",
        button_icon: str = "auto_awesome",
    ):

        with ui.card().classes(
            "glass-card option-card w-full"
        ):

            with ui.row().classes(
                "w-full items-end justify-between"
            ):

                with ui.column().classes(
                    "flex-1 gap-2"
                ):

                    ui.label(label).classes(
                        "option-label"
                    )

                    dropdown = (
                        ui.select(
                            options=options,
                            value=value,
                        )
                        .props("outlined")
                        .classes("form-select w-full")
                    )

                summarize_button = (
                    ui.button(
                        button_text,
                        icon=button_icon,
                    )
                    .classes("btn-primary")
                )

        return dropdown, summarize_button
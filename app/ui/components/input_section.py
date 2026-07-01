from nicegui import ui


class InputSection:

    @staticmethod
    def create(
        label: str = "Input Text",
        placeholder: str = "Paste your text here...",
        max_characters: int = 50000,
    ):

        with ui.column().classes("w-full gap-3"):

            ui.label(label).classes(
                "section-title"
            )

            with ui.card().classes(
                "glass-card input-card w-full"
            ):

                textarea = (
                    ui.textarea(
                        placeholder=placeholder,
                    )
                    .props("outlined autogrow")
                    .classes("form-textarea w-full")
                )

                # Give the textarea a proper height
                textarea.style(
                    "min-height:320px;"
                )

                with ui.row().classes(
                    "w-full justify-between items-center input-footer"
                ):

                    character_counter = ui.label(
                        f"0 / {max_characters} Characters"
                    ).classes(
                        "character-counter"
                    )

                    reading_time = ui.label(
                        "0 min read"
                    ).classes(
                        "reading-time"
                    )

        def update_counter():

            text = textarea.value or ""

            characters = len(text)

            words = len(text.split())

            minutes = (words + 199) // 200

            character_counter.set_text(
                f"{characters} / {max_characters} Characters"
            )

            reading_time.set_text(
                f"{minutes} min read"
            )

        textarea.on(
            "update:model-value",
            lambda e: update_counter()
        )

        return textarea
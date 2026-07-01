from nicegui import ui


class PromptExamples:

    @staticmethod
    def create():

        with ui.card().classes(
            "glass-card prompt-card"
        ):

            ui.label(
                "✨ Quick Examples"
            ).classes(
                "section-title"
            )

            with ui.row().classes(
                "prompt-grid"
            ):

                examples = [
                    (
                        "📄 Research Paper",
                        "Summarize this research paper into key findings."
                    ),
                    (
                        "📰 News Article",
                        "Summarize this news article in 5 bullet points."
                    ),
                    (
                        "💼 Meeting Notes",
                        "Create concise meeting notes with action items."
                    ),
                    (
                        "📚 Book Chapter",
                        "Summarize this chapter while preserving important concepts."
                    ),
                    (
                        "⚖ Legal Document",
                        "Summarize this legal document in simple language."
                    ),
                    (
                        "💻 Technical Documentation",
                        "Summarize the technical documentation for developers."
                    ),
                ]

                buttons = []

                for title, prompt in examples:

                    btn = (
                        ui.button(title)
                        .classes(
                            "btn-secondary prompt-button"
                        )
                    )

                    btn.prompt = prompt

                    buttons.append(btn)

        return buttons
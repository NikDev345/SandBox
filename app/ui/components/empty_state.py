from nicegui import ui


class EmptyState:

    @staticmethod
    def create():

        with ui.column().classes(
            "empty-state"
        ) as container:

            ui.icon(
                "auto_awesome"
            ).classes(
                "empty-state-icon"
            )

            ui.label(
                "Ready to Summarize"
            ).classes(
                "empty-state-title"
            )

            ui.label(
                "Paste your article, research paper, meeting notes or upload a document to generate an AI-powered summary."
            ).classes(
                "empty-state-description"
            )

            with ui.row().classes(
                "empty-state-tags"
            ):

                ui.label("📄 PDF").classes("tool-badge")
                ui.label("📝 DOCX").classes("tool-badge")
                ui.label("📚 TXT").classes("tool-badge")
                ui.label("⚡ Gemini AI").classes("tool-badge")

        return container
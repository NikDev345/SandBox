from nicegui import ui


class FileUpload:

    @staticmethod
    def create():

        with ui.card().classes("glass-card"):

            ui.label(
                "Upload Document"
            ).classes("section-title")

            upload = ui.upload(
                auto_upload=False,
                max_files=1,
            ).props(
                "accept=.pdf,.doc,.docx,.txt"
            ).classes(
                "form-input"
            )

            ui.label(
                "Supported formats: PDF, DOC, DOCX, TXT"
            ).classes(
                "text-muted"
            )

        return upload
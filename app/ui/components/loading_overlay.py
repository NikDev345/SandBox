from nicegui import ui


class LoadingOverlay:

    @staticmethod
    def create(message: str = "Generating with Gemini AI..."):

        with ui.column().classes(
            "loading-overlay"
        ) as container:

            spinner = ui.spinner(
                size="lg"
            ).classes(
                "loading-spinner"
            )

            title = ui.label(
                message
            ).classes(
                "loading-title"
            )

            subtitle = ui.label(
                "Please wait while AI processes your request..."
            ).classes(
                "loading-subtitle"
            )

            progress = ui.linear_progress(
                value=None
            ).classes(
                "loading-progress"
            )

        container.visible = False

        def show():
            container.visible = True

        def hide():
            container.visible = False

        return {
            "container": container,
            "spinner": spinner,
            "title": title,
            "subtitle": subtitle,
            "progress": progress,
            "show": show,
            "hide": hide,
        }
from nicegui import ui

from app.ui.components.tool_header import ToolHeader
from app.ui.components.input_section import InputSection
from app.ui.components.option_bar import OptionBar
from app.ui.components.output_section import OutputSection
from app.ui.components.action_buttons import ActionButtons
from app.ui.components.loading_overlay import LoadingOverlay


@ui.page("/text-summarizer")
def text_summarizer_page():

    # Center the page
    with ui.column().classes("w-full items-center"):

        # Main Container
        with ui.card().classes("glass-card w-[1100px] p-8 gap-8"):

            # ==========================================
            # Header
            # ==========================================

            ToolHeader.create(
                title="AI Text Summarizer",
                description="Summarize articles, reports and documents using Gemini AI.",
                icon="summarize",
                model="Gemini 2.5 Flash",
                category="TEXT TOOL",
            )

            ui.separator()

            # ==========================================
            # Input
            # ==========================================

            input_text = InputSection.create(
                label="Input Text",
                placeholder="Paste your text here..."
            )

            # ==========================================
            # Options
            # ==========================================

            summary_length, generate_btn = OptionBar.create(
                options=[
                    "short",
                    "medium",
                    "detailed",
                ],
                value="medium",
                label="Summary Length",
                button_text="Generate Summary",
            )

            # ==========================================
            # Loading
            # ==========================================

            loading = LoadingOverlay.create(
                "Generating summary..."
            )

            # ==========================================
            # Output
            # ==========================================

            (
                output_text,
                words,
                characters,
                reading_time,
            ) = OutputSection.create(
                label="Generated Summary",
                placeholder="Your summary will appear here..."
            )

            ui.separator()

            # ==========================================
            # Bottom Buttons
            # ==========================================

            (
                copy_btn,
                download_btn,
                history_btn,
                clear_btn,
            ) = ActionButtons.create()

            # ==========================================
            # Temporary Events
            # ==========================================

            def clear():

                input_text.set_value("")
                output_text.set_value("")

            clear_btn.on_click(clear)
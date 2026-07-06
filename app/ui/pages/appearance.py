from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.user_sidebar import user_sidebar
from app.ui.components.footer import footer


def appearance_page(user: dict):

    navbar(user)

    with ui.row().classes(
        'w-full h-[calc(100vh-64px)]'
    ):

        user_sidebar(active='appearance')

        with ui.column().classes(
            '''
            flex-1
            p-10
            gap-8
            overflow-auto
            '''
        ):

            # =====================================================
            # Header
            # =====================================================

            ui.label(
                "Appearance"
            ).classes(
                "text-4xl font-bold"
            )

            ui.label(
                "Customize how Sandbox looks and feels."
            ).classes(
                "text-slate-400 mb-6"
            )

            # =====================================================
            # Theme
            # =====================================================

            with ui.card().classes(
                "w-full rounded-3xl p-8"
            ):

                ui.label(
                    "Theme"
                ).classes(
                    "text-2xl font-semibold"
                )

                ui.label(
                    "Choose your preferred theme."
                ).classes(
                    "text-slate-400 mb-6"
                )

                theme = ui.radio(
                    {
                        "dark": "Dark",
                        "light": "Light",
                        "system": "System"
                    },
                    value="dark"
                ).props(
                    "inline"
                )

                theme.on(
                    "update:model-value",
                    lambda e:
                    ui.run_javascript(
                        f"window.setTheme('{e.value}')"
                    )
                )

            # =====================================================
            # Accent
            # =====================================================

            with ui.card().classes(
                "w-full rounded-3xl p-8"
            ):

                ui.label(
                    "Accent Color"
                ).classes(
                    "text-2xl font-semibold"
                )

                ui.label(
                    "Choose the primary color used throughout Sandbox."
                ).classes(
                    "text-slate-400 mb-6"
                )

                with ui.row().classes(
                    "gap-4"
                ):

                    colors = [

                        "#2563eb",

                        "#9333ea",

                        "#22c55e",

                        "#ef4444",

                        "#f59e0b",

                        "#06b6d4"

                    ]

                    for color in colors:

                        ui.button().style(
                            f"""
                            width:44px;
                            height:44px;
                            border-radius:999px;
                            background:{color};
                            """
                        )

            # =====================================================
            # Animations
            # =====================================================

            with ui.card().classes(
                "w-full rounded-3xl p-8"
            ):

                ui.label(
                    "Animations"
                ).classes(
                    "text-2xl font-semibold"
                )

                ui.label(
                    "Control interface animations."
                ).classes(
                    "text-slate-400 mb-6"
                )

                ui.switch(
                    "Enable animations",
                    value=True
                )

                ui.switch(
                    "Reduced motion",
                    value=False
                )

            # =====================================================
            # Sidebar
            # =====================================================

            with ui.card().classes(
                "w-full rounded-3xl p-8"
            ):

                ui.label(
                    "Sidebar"
                ).classes(
                    "text-2xl font-semibold"
                )

                ui.label(
                    "Choose your sidebar layout."
                ).classes(
                    "text-slate-400 mb-6"
                )

                ui.radio(
                    {
                        "expanded": "Expanded",

                        "compact": "Compact"

                    },
                    value="expanded"
                ).props(
                    "inline"
                )

            # =====================================================
            # Preview
            # =====================================================

            with ui.card().classes(
                "w-full rounded-3xl p-8"
            ):

                ui.label(
                    "Preview"
                ).classes(
                    "text-2xl font-semibold"
                )

                ui.label(
                    "See how your settings will look."
                ).classes(
                    "text-slate-400 mb-6"
                )

                with ui.card().classes(
                    "rounded-2xl p-6 w-full"
                ):

                    ui.label(
                        "Sandbox Preview"
                    ).classes(
                        "text-xl font-bold"
                    )

                    ui.label(
                        "This card updates with your appearance settings."
                    ).classes(
                        "text-slate-400"
                    )

                    ui.button(
                        "Primary Button"
                    )

            # =====================================================
            # Actions
            # =====================================================

            with ui.row().classes(
                "justify-end w-full mt-4 gap-4"
            ):

                ui.button(
                    "Reset"
                ).props(
                    "outline"
                )

                ui.button(
                    "Save Changes"
                )

    footer()
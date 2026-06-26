from nicegui import ui
from app.ui.components.user_dropdown import user_dropdown

def navbar(user: dict | None = None):

    with ui.header().classes(
        '''
        items-center
        justify-between
        px-6
        h-16
        bg-slate-900
        border-b
        border-slate-800
        shadow-md
        '''
    ):

        # -------------------------------------------------
        # Left
        # -------------------------------------------------

        with ui.row().classes('items-center gap-4'):

            ui.label("Sandbox").classes(
                "text-2xl font-bold text-cyan-400"
            )

            ui.input(
                placeholder="Search tools..."
            ).props(
                'outlined dense clearable'
            ).classes(
                'w-96'
            )

        # -------------------------------------------------
        # Right
        # -------------------------------------------------

        with ui.row().classes(
            'items-center gap-3'
        ):

            ui.button(
                icon='notifications_none'
            ).props(
                'flat round'
            )

            if user:

                with ui.button().props(
                    'flat round dense'
                ).classes(
                    'p-0'
                ):

                    ui.avatar().props(
                        f'image="{user["avatar"]}"'
                    ).classes(
                        'w-10 h-10'
                    )

                    with ui.menu():

                        with ui.column().classes("gap-0 p-2"):

                            ui.label(user["name"]).classes(
                                "text-base font-semibold"
                            )

                            ui.label(user["email"]).classes(
                                "text-sm text-slate-400"
                            )

                            ui.label(
                                user["provider"].capitalize()
                            ).classes(
                                "text-xs text-slate-500"
                            )

                        ui.separator()

                        ui.menu_item(
                            "Settings",
                            lambda: ui.navigate.to("/settings")
                        )

                        # -----------------------------------

                        with ui.menu_item(
                            'Appearance'
                        ):

                            ui.menu_item(
                                "Dark",
                                lambda: ui.run_javascript(
                                    "setTheme('dark')"
                                )
                            )

                            ui.menu_item(
                            "Light",
                            lambda: ui.run_javascript(
                                "setTheme('light')"
                            )
                        )

                            ui.menu_item(
                                "System",
                                lambda: ui.run_javascript(
                                    "setTheme('system')"
                                )
                        )

                        ui.separator()

                        ui.menu_item(
                            'Logout',
                            lambda: ui.navigate.to('/logout')
                        )

            else:

                ui.button(
                    'Login',
                    on_click=lambda: ui.navigate.to('/login')
                ).props(
                    'flat'
                )

                ui.button(
                    'Sign Up',
                    on_click=lambda: ui.navigate.to('/signup')
                )
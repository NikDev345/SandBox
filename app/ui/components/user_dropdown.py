from nicegui import ui


def user_dropdown(user: dict):

    with ui.button().props(
        "flat round"
    ).classes(
        "p-0"
    ):

        ui.avatar(size="42px").props(
            f'image="{user["avatar"]}"'
        )

        with ui.menu().classes(
            "w-72"
        ):

            # ----------------------------------------
            # User Info
            # ----------------------------------------

            with ui.column().classes(
                "w-full p-3 gap-1"
            ):

                ui.label(
                    user["name"]
                ).classes(
                    "text-base font-semibold"
                )

                ui.label(
                    user["email"]
                ).classes(
                    "text-sm text-slate-400"
                )

            ui.separator()

            # ----------------------------------------
            # Account
            # ----------------------------------------

            ui.menu_item(
                "User Panel",
                lambda: ui.navigate.to("/user"),
            ).props(
                'icon="person"'
            )

            ui.menu_item(
                "Appearance",
                lambda: ui.navigate.to("/user/appearance"),
            ).props(
                'icon="palette"'
            )

            ui.menu_item(
                "Security",
                lambda: ui.navigate.to("/user/security"),
            ).props(
                'icon="shield"'
            )

            ui.separator()

            # ----------------------------------------
            # Theme
            # ----------------------------------------

            ui.label(
                "Theme"
            ).classes(
                "text-xs text-slate-500 px-4 pt-2"
            )

            ui.menu_item(
                "Dark",
                lambda: ui.run_javascript(
                    "setTheme('dark')"
                ),
            ).props(
                'icon="dark_mode"'
            )

            ui.menu_item(
                "Light",
                lambda: ui.run_javascript(
                    "setTheme('light')"
                ),
            ).props(
                'icon="light_mode"'
            )

            ui.menu_item(
                "System",
                lambda: ui.run_javascript(
                    "setTheme('system')"
                ),
            ).props(
                'icon="desktop_windows"'
            )

            ui.separator()

            ui.menu_item(
                "Sign Out",
                lambda: ui.navigate.to("/logout"),
            ).props(
                'icon="logout"'
            )
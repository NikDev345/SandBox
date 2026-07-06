from nicegui import ui


def user_sidebar(active: str = "profile"):

    menu = [
        ("Profile", "/user"),
        ("Appearance", "/user/appearance"),
        ("Security", "/user/security"),
        ("Connected Accounts", "/user/connected"),
        ("Notifications", "/user/notifications"),
    ]

    with ui.column().classes(
        "w-72 h-screen bg-slate-900 border-r border-slate-800 p-6"
    ):

        ui.label("Settings").classes(
            "text-2xl font-bold text-white mb-8"
        )

        for title, link in menu:

            color = (
                "bg-cyan-600 text-white"
                if title.lower().startswith(active)
                else "text-slate-300"
            )

            ui.button(
                title,
                on_click=lambda l=link: ui.navigate.to(l)
            ).classes(
                f"w-full justify-start rounded-xl mb-2 {color}"
            )

        ui.separator()

        ui.button(
            "Logout",
            icon="logout",
            color="red"
        ).classes(
            "w-full mt-4"
        )
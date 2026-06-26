from nicegui import ui


def account_overview(user: dict):

    with ui.grid(columns=2).classes(
        "w-full gap-6"
    ):

        # ----------------------------
        # Profile
        # ----------------------------

        with ui.card().classes(
            "bg-slate-900 rounded-2xl p-6 border border-slate-800"
        ):

            ui.label(
                "Profile"
            ).classes(
                "text-xl font-semibold text-white"
            )

            ui.separator()

            ui.label(
                f"Name: {user['name']}"
            ).classes(
                "text-white"
            )

            ui.label(
                f"Email: {user['email']}"
            ).classes(
                "text-slate-300"
            )

            ui.label(
                f"Role: {user['role']}"
            ).classes(
                "text-slate-300"
            )

        # ----------------------------
        # Authentication
        # ----------------------------

        with ui.card().classes(
            "bg-slate-900 rounded-2xl p-6 border border-slate-800"
        ):

            ui.label(
                "Authentication"
            ).classes(
                "text-xl font-semibold text-white"
            )

            ui.separator()

            ui.label(
                f"Provider: {user['provider']}"
            ).classes(
                "text-white"
            )

            ui.label(
                "Status: Signed In"
            ).classes(
                "text-green-400"
            )

        # ----------------------------
        # Connected Accounts
        # ----------------------------

        with ui.card().classes(
            "bg-slate-900 rounded-2xl p-6 border border-slate-800"
        ):

            ui.label(
                "Connected Accounts"
            ).classes(
                "text-xl font-semibold text-white"
            )

            ui.separator()

            google = "✅" if user["provider"] == "google" else "➕"

            github = "✅" if user["provider"] == "github" else "➕"

            ui.label(f"{google} Google").classes("text-white")

            ui.label(f"{github} GitHub").classes("text-white")

        # ----------------------------
        # Quick Actions
        # ----------------------------

        with ui.card().classes(
            "bg-slate-900 rounded-2xl p-6 border border-slate-800"
        ):

            ui.label(
                "Quick Actions"
            ).classes(
                "text-xl font-semibold text-white"
            )

            ui.separator()

            ui.button(
                "Appearance",
                icon="palette"
            )

            ui.button(
                "Security",
                icon="shield"
            )

            ui.button(
                "Notifications",
                icon="notifications"
            )
from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer
from app.ui.components.user_sidebar import user_sidebar
from app.ui.components.user_header import user_header
from app.ui.components.profile_section import profile_section
from app.ui.components.account_overview import account_overview

from app.services.auth_service import AuthService
from app.database.engine import SessionLocal


@ui.page("/user")
def user_page():

    db = SessionLocal()

    # Change this to your actual logged-in user retrieval
    current_user = ui.context.client.storage.user.get("user")

    if not current_user:
        ui.navigate.to("/login")
        return

    user = AuthService.get_profile(
        db,
        current_user
    )

    navbar(user)

    with ui.row().classes(
        "w-full h-[calc(100vh-64px)] bg-slate-950"
    ):

        user_sidebar(active="profile")

        with ui.column().classes(
            "flex-1 p-8 overflow-auto gap-6"
        ):

            user_header(
                "User Panel",
                "Manage your Sandbox account."
            )

            profile_section(user)

            account_overview(user)

    footer()

    db.close()
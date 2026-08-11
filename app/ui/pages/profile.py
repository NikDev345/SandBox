# app/ui/pages/profile.py

from nicegui import ui
from app.ui.seo import PRIVATE_PAGES, add_private_seo

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer


@ui.page('/profile', title=f"{PRIVATE_PAGES['/profile']} - SandBox")
def profile_page():
    add_private_seo("/profile")

    navbar()

    with ui.column().classes(
        'w-full items-center p-10'
    ):

        ui.label(
            'Profile'
        ).classes(
            'text-4xl font-bold'
        )

        ui.label(
            'Email: demo@example.com'
        )

        ui.label(
            'Provider: Google'
        )

        ui.label(
            'History Count: 0'
        )

        ui.label(
            'Bookmarks Count: 0'
        )

        ui.button(
            'Logout'
        )

    footer()

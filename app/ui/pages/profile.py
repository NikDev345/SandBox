# app/ui/pages/profile.py

from nicegui import ui

from app.ui.components.navbar import navbar
from app.ui.components.footer import footer


@ui.page('/profile')
def profile_page():

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
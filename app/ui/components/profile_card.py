from nicegui import ui


def profile_card(user: dict):

    with ui.card().classes(
        """
        w-full
        bg-slate-900
        rounded-3xl
        border
        border-slate-800
        shadow-xl
        p-8
        """
    ):

        # --------------------------------------------------
        # Cover Banner
        # --------------------------------------------------

        ui.image(
            "https://picsum.photos/1200/250"
        ).classes(
            "w-full h-48 rounded-2xl object-cover"
        )

        # --------------------------------------------------
        # Avatar + Details
        # --------------------------------------------------

        with ui.row().classes(
            "w-full items-end -mt-16 px-8"
        ):

            ui.avatar(size="140px").classes(
                "border-4 border-slate-900 shadow-xl"
            ).props(
                f'image="{user["avatar"]}"'
            )

            with ui.column().classes(
                "ml-6"
            ):

                ui.label(
                    user["name"]
                ).classes(
                    "text-3xl font-bold text-white"
                )

                ui.label(
                    user["email"]
                ).classes(
                    "text-slate-400"
                )

                with ui.row():

                    ui.badge(
                        user["provider"].capitalize(),
                        color="primary"
                    )

                    ui.badge(
                        user["role"].capitalize(),
                        color="green"
                    )

        ui.separator().classes(
            "my-6"
        )

        # --------------------------------------------------
        # Information
        # --------------------------------------------------

        with ui.grid(columns=2).classes(
            "gap-6"
        ):

            ui.input(
                "Full Name",
                value=user["name"]
            ).classes(
                "w-full"
            )

            ui.input(
                "Email",
                value=user["email"]
            ).classes(
                "w-full"
            )

            ui.input(
                "Provider",
                value=user["provider"]
            ).props(
                "readonly"
            )

            ui.input(
                "Role",
                value=user["role"]
            ).props(
                "readonly"
            )

        ui.separator().classes(
            "my-6"
        )

        with ui.row().classes(
            "justify-end w-full"
        ):

            ui.button(
                "Change Avatar",
                icon="photo_camera"
            ).props(
                "outline"
            )

            ui.button(
                "Save Changes",
                icon="save"
            )
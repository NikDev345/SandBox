from nicegui import ui


def profile_section(user: dict):

    with ui.card().classes(
        '''
        w-full
        rounded-[24px]
        p-0
        overflow-hidden
        bg-[var(--bg-panel)]
        border
        border-[var(--border-1)]
        shadow-xl
        '''
    ):

        # ------------------------------------------------
        # Cover
        # ------------------------------------------------

        with ui.element('div').classes(
            '''
            w-full
            h-56
            bg-gradient-to-r
            from-slate-900
            via-slate-800
            to-slate-900
            '''
        ):
            pass

        # ------------------------------------------------
        # Profile
        # ------------------------------------------------

        with ui.row().classes(
            '''
            w-full
            px-10
            -mt-16
            items-end
            '''
        ):

            ui.avatar(size='140px').classes(
                '''
                border-4
                border-slate-900
                shadow-2xl
                '''
            ).props(
                f'image="{user["avatar"]}"'
            )

            with ui.column().classes(
                'ml-6 gap-1'
            ):

                ui.label(
                    user["name"]
                ).classes(
                    'text-4xl font-bold'
                )

                ui.label(
                    user["email"]
                ).classes(
                    'text-[var(--text-muted)]'
                )

                with ui.row().classes(
                    'gap-2 mt-2'
                ):

                    ui.badge(
                        user["provider"].capitalize()
                    ).props(
                        'outline'
                    )

                    ui.badge(
                        user["role"].capitalize()
                    ).props(
                        'outline'
                    )

        ui.separator()

        # ------------------------------------------------
        # Details
        # ------------------------------------------------

        with ui.grid(columns=2).classes(
            '''
            w-full
            gap-6
            p-10
            '''
        ):

            ui.input(
                label='Full Name',
                value=user["name"]
            ).classes('w-full')

            ui.input(
                label='Email',
                value=user["email"]
            ).props(
                'readonly'
            ).classes('w-full')

            ui.input(
                label='Authentication Provider',
                value=user["provider"]
            ).props(
                'readonly'
            ).classes('w-full')

            ui.input(
                label='Role',
                value=user["role"]
            ).props(
                'readonly'
            ).classes('w-full')

        ui.separator()

        with ui.row().classes(
            '''
            w-full
            justify-end
            p-6
            gap-4
            '''
        ):

            ui.button(
                'Change Avatar',
                icon='photo_camera'
            ).props(
                'outline'
            )

            ui.button(
                'Save Changes',
                icon='save'
            )
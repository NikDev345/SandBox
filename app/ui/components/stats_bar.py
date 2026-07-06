from nicegui import ui


class StatsBar:

    @staticmethod
    def create():

        with ui.row().classes(
            "stats-bar"
        ):

            characters = ui.label(
                "0 Characters"
            ).classes(
                "stat-chip"
            )

            words = ui.label(
                "0 Words"
            ).classes(
                "stat-chip"
            )

            reading_time = ui.label(
                "0 Min Read"
            ).classes(
                "stat-chip"
            )

            tokens = ui.label(
                "0 Tokens"
            ).classes(
                "stat-chip"
            )

        return {
            "characters": characters,
            "words": words,
            "reading_time": reading_time,
            "tokens": tokens,
        }
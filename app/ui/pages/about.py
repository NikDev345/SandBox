from nicegui import ui

from app.ui.seo import PUBLIC_PAGES, add_page_seo
from app.ui.layout import page_layout


@ui.page("/about", title=PUBLIC_PAGES["/about"]["title"])
def about_page():

    add_page_seo("/about")

    page_layout()

    # ============================================================
    # ABOUT SANDBox
    # ============================================================

    with ui.column().classes(
        "w-full max-w-6xl mx-auto px-6 py-16 gap-12"
    ):

        # --------------------------------------------------------
        # HERO
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full items-center text-center gap-4"
        ):

            ui.label("ABOUT SANDBox").classes(
                "text-sm tracking-[0.3em] font-semibold opacity-70"
            )

            ui.label(
                "AI tools built by developers, for people who build."
            ).classes(
                "text-4xl md:text-6xl font-bold leading-tight"
            )

            ui.label(
                "SandBox is an AI-powered software platform created "
                "to bring practical developer, productivity, learning "
                "and content tools into one workspace."
            ).classes(
                "text-lg md:text-xl opacity-75 max-w-3xl leading-relaxed"
            )


        # --------------------------------------------------------
        # WHAT IS SANDBOX
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full gap-5"
        ):

            ui.label("What is SandBox?").classes(
                "text-3xl font-bold"
            )

            ui.label(
                "SandBox is a web-based AI software platform that "
                "combines practical artificial intelligence tools "
                "into a single workspace. Instead of requiring users "
                "to search for a separate service for every small task, "
                "SandBox brings tools for development, learning, "
                "productivity, content processing and problem solving "
                "together in one platform."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.label(
                "The platform is designed around a simple idea: "
                "AI should be useful, accessible and integrated into "
                "real workflows."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )


        # --------------------------------------------------------
        # OUR MISSION
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full gap-5"
        ):

            ui.label("Our Mission").classes(
                "text-3xl font-bold"
            )

            ui.label(
                "The goal of SandBox is to make useful AI capabilities "
                "available through focused tools that solve specific "
                "problems."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.label(
                "SandBox focuses on practical applications of "
                "artificial intelligence rather than building AI "
                "simply for the sake of using AI."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )


        # --------------------------------------------------------
        # WHAT SANDBOX PROVIDES
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full gap-6"
        ):

            ui.label("What SandBox Provides").classes(
                "text-3xl font-bold"
            )

            tools = [
                (
                    "AI Developer Tools",
                    "Tools for developers including JSON repair, "
                    "SQL generation, code review, regex generation, "
                    "Docker configuration and Git workflow assistance."
                ),
                (
                    "AI Productivity Tools",
                    "Tools that help users summarize information, "
                    "rewrite content, organize notes and work with "
                    "information more efficiently."
                ),
                (
                    "AI Learning Tools",
                    "Tools such as ELI5 explanations, quiz generation "
                    "and flashcard generation designed to make learning "
                    "and revision easier."
                ),
                (
                    "AI Content Tools",
                    "AI-powered utilities for working with text, "
                    "documents, screenshots, charts and online content."
                ),
                (
                    "Data Extraction Tools",
                    "Tools for extracting useful information from "
                    "images, documents and structured or semi-structured "
                    "content."
                ),
            ]

            for title, description in tools:

                with ui.column().classes(
                    "w-full rounded-2xl p-6 "
                    "bg-white/5 border border-white/10 gap-2"
                ):

                    ui.label(title).classes(
                        "text-xl font-semibold"
                    )

                    ui.label(description).classes(
                        "opacity-75 leading-relaxed"
                    )


        # --------------------------------------------------------
        # TECHNOLOGY
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full gap-5"
        ):

            ui.label("Technology").classes(
                "text-3xl font-bold"
            )

            ui.label(
                "SandBox is engineered as a modern AI software "
                "platform combining a web interface, backend APIs, "
                "database infrastructure and AI services."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            technologies = [
                "Python",
                "FastAPI",
                "NiceGUI",
                "SQLAlchemy",
                "PostgreSQL",
                "Artificial Intelligence",
                "Machine Learning",
                "Natural Language Processing",
                "Google Gemini",
                "PaddleOCR",
            ]

            with ui.row().classes(
                "w-full flex-wrap gap-3"
            ):

                for technology in technologies:

                    ui.label(technology).classes(
                        "px-4 py-2 rounded-full "
                        "bg-white/5 border border-white/10 "
                        "text-sm"
                    )


        # --------------------------------------------------------
        # BUILT BY
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full gap-6"
        ):

            ui.label("Built By").classes(
                "text-3xl font-bold"
            )

            ui.label(
                "SandBox is built by developers who are interested "
                "in artificial intelligence, software engineering "
                "and turning technical ideas into practical products."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )


        # --------------------------------------------------------
        # NAGRAJ
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full rounded-3xl p-8 "
            "bg-white/5 border border-white/10 gap-5"
        ):

            ui.label(
                "Nagraj Rangarej"
            ).classes(
                "text-3xl font-bold"
            )

            ui.label(
                "AI & Data Science Developer"
            ).classes(
                "text-lg font-semibold opacity-80"
            )

            ui.label(
                "Nagraj Rangarej is an AI and Data Science "
                "engineering student and software developer "
                "focused on artificial intelligence, machine "
                "learning, data science and practical software "
                "development."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.label(
                "He is the primary developer identity associated "
                "with SandBox and is involved in building the "
                "platform, its AI-powered tools and its underlying "
                "software systems."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.label(
                "His technical interests include artificial "
                "intelligence, machine learning, data science, "
                "software development, developer tools and "
                "AI-powered applications."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.link(
                "View Nagraj's Developer Profile",
                "/developers/nagraj-rangarej"
            ).classes(
                "text-sm font-semibold"
            )


        # --------------------------------------------------------
        # MITANSH
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full rounded-3xl p-8 "
            "bg-white/5 border border-white/10 gap-5"
        ):

            ui.label(
                "Mitansh Rathi"
            ).classes(
                "text-3xl font-bold"
            )

            ui.label(
                "Software & AI Developer"
            ).classes(
                "text-lg font-semibold opacity-80"
            )

            ui.label(
                "Mitansh Rathi is a software and AI developer "
                "working on backend systems, AI-powered developer "
                "tools and product engineering."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.label(
                "His work includes backend engineering, API "
                "development, AI integration, automation and "
                "building practical software systems."
            ).classes(
                "text-base md:text-lg opacity-80 leading-relaxed"
            )

            ui.link(
                "View Mitansh's Developer Profile",
                "/developers/mitansh-rathi"
            ).classes(
                "text-sm font-semibold"
            )


        # --------------------------------------------------------
        # CLOSING
        # --------------------------------------------------------

        with ui.column().classes(
            "w-full items-center text-center gap-4 py-8"
        ):

            ui.label(
                "Building practical software with AI."
            ).classes(
                "text-2xl md:text-3xl font-bold"
            )

            ui.label(
                "SandBox continues to evolve as a platform for "
                "developers, students, creators and anyone looking "
                "for practical AI-powered tools."
            ).classes(
                "max-w-2xl opacity-75 leading-relaxed"
            )
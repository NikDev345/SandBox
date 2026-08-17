from nicegui import ui

from app.ui.seo import PUBLIC_PAGES, add_page_seo


@ui.page(
    "/developers/nagraj-rangarej",
    title=PUBLIC_PAGES["/developers/nagraj-rangarej"]["title"],
)
def nagraj_profile_page():

    # ============================================================
    # SEO
    # ============================================================

    add_page_seo("/developers/nagraj-rangarej")

    # ============================================================
    # PAGE-SPECIFIC DESIGN
    # ============================================================

    ui.add_head_html(
        """
        <style>

        .developer-page {
            min-height: 100vh;
            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(34, 211, 238, 0.08),
                    transparent 34%
                ),
                #0a0a0f;
            color: #f5f5f7;
        }

        .developer-shell {
            width: min(1120px, calc(100% - 40px));
            margin: 0 auto;
        }

        .developer-topbar {
            width: min(1120px, calc(100% - 40px));
            margin: 0 auto;
            padding: 24px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .developer-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #f5f5f7;
            font-weight: 700;
            font-size: 20px;
        }

        .developer-brand-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #22d3ee;
            box-shadow: 0 0 18px rgba(34, 211, 238, 0.7);
        }

        .developer-back {
            color: rgba(255,255,255,.68);
            text-decoration: none;
            font-size: 14px;
            padding: 9px 15px;
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 999px;
            background: rgba(255,255,255,.035);
            transition: .2s ease;
        }

        .developer-back:hover {
            color: #fff;
            border-color: rgba(34,211,238,.35);
            background: rgba(34,211,238,.06);
        }

        .developer-hero {
            position: relative;
            text-align: center;
            padding: 70px 20px 90px;
        }

        .developer-avatar {
            width: 156px;
            height: 156px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid rgba(255,255,255,.14);
            box-shadow:
                0 0 0 8px rgba(255,255,255,.018),
                0 20px 70px rgba(0,0,0,.45),
                0 0 50px rgba(34,211,238,.10);
        }

        .developer-eyebrow {
            margin-top: 28px;
            font-size: 11px;
            letter-spacing: .32em;
            text-transform: uppercase;
            color: rgba(255,255,255,.48);
            font-weight: 700;
        }

        .developer-name {
            margin-top: 14px;
            font-size: clamp(42px, 7vw, 76px);
            line-height: 1;
            font-weight: 800;
            letter-spacing: -0.045em;
        }

        .developer-role {
            margin-top: 18px;
            font-size: 20px;
            color: rgba(255,255,255,.78);
            font-weight: 600;
        }

        .developer-tagline {
            max-width: 700px;
            margin: 18px auto 0;
            color: rgba(255,255,255,.56);
            font-size: 17px;
            line-height: 1.75;
        }

        .developer-actions {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 28px;
        }

        .developer-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 120px;
            padding: 11px 18px;
            border-radius: 999px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            color: #fff;
            background: rgba(255,255,255,.055);
            border: 1px solid rgba(255,255,255,.11);
            transition: .2s ease;
        }

        .developer-button:hover {
            transform: translateY(-1px);
            border-color: rgba(34,211,238,.4);
            background: rgba(34,211,238,.07);
        }

        .developer-button-primary {
            border-color: rgba(34,211,238,.3);
            background: rgba(34,211,238,.08);
        }

        .developer-section {
            margin-bottom: 72px;
        }

        .developer-section-label {
            margin-bottom: 10px;
            color: #22d3ee;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .24em;
            text-transform: uppercase;
        }

        .developer-section-title {
            font-size: 32px;
            font-weight: 750;
            letter-spacing: -.025em;
            margin-bottom: 18px;
        }

        .developer-section-text {
            color: rgba(255,255,255,.62);
            font-size: 16px;
            line-height: 1.85;
            max-width: 850px;
        }

        .developer-card {
            height: 100%;
            padding: 26px;
            border-radius: 20px;
            background: rgba(255,255,255,.035);
            border: 1px solid rgba(255,255,255,.085);
            box-shadow: 0 16px 45px rgba(0,0,0,.14);
            transition: .2s ease;
        }

        .developer-card:hover {
            transform: translateY(-3px);
            border-color: rgba(34,211,238,.20);
            background: rgba(255,255,255,.045);
        }

        .developer-card-title {
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 9px;
        }

        .developer-card-text {
            color: rgba(255,255,255,.54);
            line-height: 1.7;
            font-size: 14px;
        }

        .developer-skill {
            padding: 9px 14px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,.09);
            background: rgba(255,255,255,.035);
            color: rgba(255,255,255,.72);
            font-size: 13px;
        }

        .developer-sandbox {
            padding: 38px;
            border-radius: 24px;
            border: 1px solid rgba(34,211,238,.13);
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(34,211,238,.07),
                    transparent 35%
                ),
                rgba(255,255,255,.035);
        }

        .developer-project {
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,.075);
            background: rgba(255,255,255,.028);
        }

        .developer-project-title {
            font-size: 14px;
            font-weight: 650;
        }

        .developer-footer {
            padding: 50px 20px 35px;
            text-align: center;
            border-top: 1px solid rgba(255,255,255,.07);
            color: rgba(255,255,255,.42);
        }

        .developer-footer-brand {
            color: rgba(255,255,255,.85);
            font-weight: 700;
            font-size: 18px;
        }

        @media (max-width: 640px) {

            .developer-shell {
                width: min(100% - 28px, 1120px);
            }

            .developer-topbar {
                width: min(100% - 28px, 1120px);
            }

            .developer-hero {
                padding-top: 48px;
                padding-bottom: 65px;
            }

            .developer-avatar {
                width: 128px;
                height: 128px;
            }

            .developer-section-title {
                font-size: 27px;
            }

            .developer-sandbox {
                padding: 25px;
            }

        }

        </style>
        """
    )

    # ============================================================
    # PAGE
    # ============================================================

    with ui.column().classes(
        "developer-page w-full gap-0"
    ):

        # ========================================================
        # TOP BAR
        # ========================================================

        with ui.row().classes(
            "developer-topbar"
        ):

            ui.link(
                "SandBox",
                "/",
            ).classes(
                "developer-brand"
            )

            ui.link(
                "← Back to SandBox",
                "/",
            ).classes(
                "developer-back"
            )

        # ========================================================
        # HERO
        # ========================================================

        with ui.column().classes(
            "developer-shell developer-hero items-center"
        ):

            ui.image(
                "/assets/developers/nagraj.png"
            ).classes(
                "developer-avatar"
            )

            ui.label(
                "Developer Profile"
            ).classes(
                "developer-eyebrow"
            )

            ui.label(
                "Nagraj Rangarej"
            ).classes(
                "developer-name"
            )

            ui.label(
                "AI & Data Science Developer"
            ).classes(
                "developer-role"
            )

            ui.label(
                "Building practical AI systems, developer tools "
                "and software products through SandBox."
            ).classes(
                "developer-tagline"
            )

            with ui.row().classes(
                "developer-actions"
            ):

                ui.link(
                    "GitHub",
                    "https://github.com/NikDev345",
                ).classes(
                    "developer-button"
                )

                ui.link(
                    "Explore SandBox",
                    "/",
                ).classes(
                    "developer-button developer-button-primary"
                )

        # ========================================================
        # MAIN CONTENT
        # ========================================================

        with ui.column().classes(
            "developer-shell"
        ):

            # ----------------------------------------------------
            # ABOUT
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "01 / About"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Who is Nagraj Rangarej?"
                ).classes(
                    "developer-section-title"
                )

                ui.label(
                    "Nagraj Rangarej is an AI and Data Science "
                    "engineering student and software developer "
                    "focused on artificial intelligence, machine "
                    "learning, data science and practical software "
                    "development."
                ).classes(
                    "developer-section-text"
                )

                ui.label(
                    "His approach to development is strongly "
                    "practical: turning technical ideas into usable "
                    "software, integrating AI into applications and "
                    "building systems that solve real problems."
                ).classes(
                    "developer-section-text mt-4"
                )

            # ----------------------------------------------------
            # SANDBOX
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section developer-sandbox"
            ):

                ui.label(
                    "02 / SandBox"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Building SandBox"
                ).classes(
                    "developer-section-title"
                )

                ui.label(
                    "SandBox is an AI-powered software platform "
                    "designed to bring practical AI tools for "
                    "developers, students and creators into one "
                    "online workspace."
                ).classes(
                    "developer-section-text"
                )

                ui.label(
                    "Nagraj is the primary developer identity "
                    "associated with SandBox and works across the "
                    "platform's AI tools, backend systems, "
                    "integrations and product implementation."
                ).classes(
                    "developer-section-text mt-4"
                )

                with ui.row().classes(
                    "developer-actions justify-start"
                ):

                    ui.link(
                        "Open SandBox →",
                        "/",
                    ).classes(
                        "developer-button developer-button-primary"
                    )

            # ----------------------------------------------------
            # EXPERTISE
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "03 / Expertise"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Technical Expertise"
                ).classes(
                    "developer-section-title"
                )

                skills = [
                    (
                        "Artificial Intelligence",
                        "Building practical AI-powered applications "
                        "and integrating AI capabilities into software."
                    ),
                    (
                        "Data Science",
                        "Working with data processing, analysis and "
                        "AI/Data Science applications."
                    ),
                    (
                        "Machine Learning",
                        "Applied machine-learning workflows and "
                        "practical model-driven solutions."
                    ),
                    (
                        "Python",
                        "AI, backend development, automation and "
                        "software implementation."
                    ),
                    (
                        "Java",
                        "Programming and general software development."
                    ),
                    (
                        "SQL",
                        "Relational databases, data access and "
                        "application data systems."
                    ),
                    (
                        "Backend Development",
                        "Building API-driven software systems and "
                        "backend services."
                    ),
                    (
                        "AI Developer Tools",
                        "Combining AI with developer and productivity "
                        "workflows."
                    ),
                ]

                with ui.grid().classes(
                    "w-full grid-cols-1 md:grid-cols-2 gap-4"
                ):

                    for title, description in skills:

                        with ui.column().classes(
                            "developer-card"
                        ):

                            ui.label(
                                title
                            ).classes(
                                "developer-card-title"
                            )

                            ui.label(
                                description
                            ).classes(
                                "developer-card-text"
                            )

            # ----------------------------------------------------
            # TECHNOLOGIES
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "04 / Technologies"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Technology Stack"
                ).classes(
                    "developer-section-title"
                )

                technologies = [
                    "Python",
                    "Java",
                    "SQL",
                    "FastAPI",
                    "NiceGUI",
                    "SQLAlchemy",
                    "PostgreSQL",
                    "Machine Learning",
                    "Natural Language Processing",
                    "Google Gemini",
                    "PaddleOCR",
                ]

                with ui.row().classes(
                    "w-full flex-wrap gap-2"
                ):

                    for technology in technologies:

                        ui.label(
                            technology
                        ).classes(
                            "developer-skill"
                        )

            # ----------------------------------------------------
            # SANDBOX WORK
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "05 / Work"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Work on SandBox"
                ).classes(
                    "developer-section-title"
                )

                ui.label(
                    "Nagraj's work on SandBox spans AI-powered "
                    "developer, productivity, learning and data "
                    "processing tools."
                ).classes(
                    "developer-section-text"
                )

                projects = [
                    "AI Text Summarization",
                    "JSON Repair",
                    "Image Text Extraction / OCR",
                    "Table Extraction",
                    "ELI5 Explanations",
                    "AI Quiz Generation",
                    "AI Flashcard Generation",
                    "YouTube Summarization",
                    "SQL Generation",
                    "Regex Generation",
                    "AI Code Review",
                    "Error Explanation",
                    "Git Commit Assistance",
                    "Docker Configuration",
                    "API Mock Generation",
                    "AI Productivity Tools",
                ]

                with ui.grid().classes(
                    "w-full grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 mt-6"
                ):

                    for project in projects:

                        with ui.column().classes(
                            "developer-project"
                        ):

                            ui.label(
                                project
                            ).classes(
                                "developer-project-title"
                            )

            # ----------------------------------------------------
            # DEVELOPMENT APPROACH
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "06 / Approach"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "How I Build"
                ).classes(
                    "developer-section-title"
                )

                ui.label(
                    "Nagraj approaches development through building, "
                    "testing, debugging and continuously improving "
                    "real systems."
                ).classes(
                    "developer-section-text"
                )

                ui.label(
                    "The focus is on practical implementation: "
                    "connecting AI models with software systems, "
                    "building useful interfaces, integrating APIs "
                    "and databases, and turning technical ideas "
                    "into usable products."
                ).classes(
                    "developer-section-text mt-4"
                )

            # ----------------------------------------------------
            # INTERESTS
            # ----------------------------------------------------

            with ui.column().classes(
                "developer-section"
            ):

                ui.label(
                    "07 / Interests"
                ).classes(
                    "developer-section-label"
                )

                ui.label(
                    "Areas of Interest"
                ).classes(
                    "developer-section-title"
                )

                interests = [
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Data Science",
                    "AI Applications",
                    "Developer Tools",
                    "Software Engineering",
                    "Natural Language Processing",
                    "AI Systems",
                    "Automation",
                    "Emerging Technology",
                ]

                with ui.row().classes(
                    "w-full flex-wrap gap-2"
                ):

                    for interest in interests:

                        ui.label(
                            interest
                        ).classes(
                            "developer-skill"
                        )

        # ========================================================
        # FOOTER
        # ========================================================

        with ui.column().classes(
            "developer-footer w-full"
        ):

            ui.label(
                "SandBox"
            ).classes(
                "developer-footer-brand"
            )

            ui.label(
                "AI tools. One workspace."
            ).classes(
                "mt-2"
            )

            ui.label(
                "Nagraj Rangarej • AI & Data Science Developer"
            ).classes(
                "mt-3 text-sm"
            )

            ui.link(
                "Back to SandBox",
                "/",
            ).classes(
                "developer-back mt-5"
            )
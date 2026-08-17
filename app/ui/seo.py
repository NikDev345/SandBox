import html
import json
import os
from urllib.parse import urljoin

from nicegui import ui


# ============================================================
# SANDBox SEO CONFIGURATION
# ============================================================

CANONICAL_BASE_URL = "https://sandboxhome.online"
SITE_NAME = "SandBox"

# Main brand assets
DEFAULT_IMAGE_PATH = "/assets/logo.png"

# Public identity pages
ABOUT_PATH = "/about"
DEVELOPER_PATH = "/developers/nagraj-rangarej"

# ============================================================
# BRAND / ORGANIZATION IDENTITY
# ============================================================

ORGANIZATION_ID = f"{CANONICAL_BASE_URL}/#organization"
WEBSITE_ID = f"{CANONICAL_BASE_URL}/#website"
APPLICATION_ID = f"{CANONICAL_BASE_URL}/#application"

NAGRAJ_ID = f"{CANONICAL_BASE_URL}/developers/nagraj-rangarej#person"
MITANSH_ID = f"{CANONICAL_BASE_URL}/developers/mitansh-rathi#person"


# ============================================================
# BASE URL HELPERS
# ============================================================

def _base_url() -> str:
    return (
        os.getenv("APP_BASE_URL")
        or CANONICAL_BASE_URL
    ).rstrip("/")


def absolute_url(path: str = "/") -> str:
    return urljoin(
        f"{_base_url()}/",
        path.lstrip("/")
    )


# ============================================================
# HTML HELPERS
# ============================================================

def _meta_attrs(attrs: dict[str, str]) -> str:
    return " ".join(
        f'{name}="{html.escape(value, quote=True)}"'
        for name, value in attrs.items()
    )


def _tag(name: str, attrs: dict[str, str]) -> str:
    return f"<{name} {_meta_attrs(attrs)}>"


def _json_ld(data) -> str:
    """
    Safely serialize JSON-LD for insertion into <head>.
    """
    return (
        '<script type="application/ld+json">'
        + json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":")
        )
        + "</script>"
    )


# ============================================================
# PUBLIC PAGE SEO
# ============================================================

PUBLIC_PAGES = {

    # --------------------------------------------------------
    # HOMEPAGE
    # --------------------------------------------------------

    "/": {
        "title": (
            "SandBox - AI Tools for Developers, "
            "Students & Creators"
        ),
        "description": (
            "SandBox is an AI-powered software platform "
            "built by developers to help students, developers "
            "and creators work, learn, build and solve problems "
            "with practical AI tools."
        ),
    },

    # --------------------------------------------------------
    # ABOUT / DEVELOPER IDENTITY
    # --------------------------------------------------------

    "/about": {
        "title": (
            "About SandBox - AI Platform Built by Developers"
        ),
        "description": (
            "Learn about SandBox, the AI-powered software "
            "platform built by Nagraj Rangarej and the "
            "development team behind its AI, developer and "
            "productivity tools."
        ),
    },

    "/developers/nagraj-rangarej": {
        "title": (
            "Nagraj Rangarej - AI & Data Science Developer | SandBox"
        ),
        "description": (
            "Nagraj Rangarej is an AI and Data Science engineering "
            "student and developer building SandBox, an AI-powered "
            "software platform featuring practical developer, "
            "productivity, learning and automation tools."
        ),
    },

    "/developers/mitansh-rathi": {
        "title": (
            "Mitansh Rathi - Software & AI Developer | SandBox"
        ),
        "description": (
            "Mitansh Rathi is a software and AI developer working "
            "on backend systems, AI-powered developer tools and "
            "product engineering for SandBox."
        ),
    },

    # --------------------------------------------------------
    # EXISTING TOOLS
    # --------------------------------------------------------

    "/json-fixer": {
        "title": (
            "JSON Fixer - Repair Invalid JSON Online | SandBox"
        ),
        "description": (
            "Fix malformed JSON, clean syntax errors, and turn "
            "broken JSON into usable structured data with "
            "SandBox's AI JSON Fixer."
        ),
    },

    "/text-summarizer": {
        "title": (
            "Text Summarizer - Summarize PDFs and Text | SandBox"
        ),
        "description": (
            "Summarize pasted text or PDF content into clear, "
            "structured notes with SandBox's AI Text Summarizer."
        ),
    },

    "/image-text-extractor": {
        "title": (
            "Image Text Extractor - OCR from Images | SandBox"
        ),
        "description": (
            "Extract readable text from images, screenshots and "
            "photos with SandBox's AI-powered OCR tool."
        ),
    },

    "/eli5": {
        "title": (
            "ELI5 Explainer - Explain Complex Topics Simply | SandBox"
        ),
        "description": (
            "Turn complex ideas into simple explanations with "
            "SandBox's AI ELI5 tool for students, developers, "
            "creators and curious learners."
        ),
    },

    "/ss_explain": {
        "title": (
            "Screenshot Explainer - Understand Images with AI | SandBox"
        ),
        "description": (
            "Upload a screenshot and get a clear AI explanation "
            "of visual content, interfaces, charts, errors or documents."
        ),
    },

    "/sql_gen": {
        "title": (
            "SQL Generator - Create SQL from Plain English | SandBox"
        ),
        "description": (
            "Generate SQL queries from natural language prompts "
            "with SandBox's AI SQL Generator for faster database work."
        ),
    },

    "/table_extractor": {
        "title": (
            "AI Table Extractor - Extract Tables from PDFs and Images | SandBox"
        ),
        "description": (
            "Extract structured tables from PDFs and images and "
            "convert them into useful data with SandBox."
        ),
    },

    "/notes_cleaner": {
        "title": (
            "Notes Cleaner - Clean and Organize Notes | SandBox"
        ),
        "description": (
            "Clean messy notes, improve readability and organize "
            "study or work material with SandBox's AI Notes Cleaner."
        ),
    },

    "/mock_api": {
        "title": (
            "Mock API Generator - Create Fake API Endpoints | SandBox"
        ),
        "description": (
            "Create realistic mock API endpoints for testing, "
            "prototyping and frontend development with SandBox."
        ),
    },

    "/chart-explainer": {
        "title": (
            "Chart Explainer - Explain Charts with AI | SandBox"
        ),
        "description": (
            "Upload or describe a chart and get a clear AI "
            "explanation of trends, patterns and insights."
        ),
    },

    "/email-rewriter": {
        "title": (
            "Email Rewriter - Improve Emails with AI | SandBox"
        ),
        "description": (
            "Rewrite emails for tone, clarity and professionalism "
            "with SandBox's AI Email Rewriter."
        ),
    },

    "/blog-outline-generator": {
        "title": (
            "Blog Outline Generator - Plan Blog Posts with AI | SandBox"
        ),
        "description": (
            "Generate structured blog outlines, headings and "
            "content direction for articles with SandBox."
        ),
    },

    "/pro_cons_gen": {
        "title": (
            "Pros and Cons Generator - Compare Decisions | SandBox"
        ),
        "description": (
            "Generate balanced pros and cons for topics, ideas "
            "and decisions with SandBox's AI comparison tool."
        ),
    },

    "/quiz-generator": {
        "title": (
            "Quiz Generator - Create Quizzes with AI | SandBox"
        ),
        "description": (
            "Create quizzes from topics or documents with "
            "SandBox's AI Quiz Generator for learning and review."
        ),
    },

    "/flashcard-generator": {
        "title": (
            "Flashcard Generator - Make Study Flashcards | SandBox"
        ),
        "description": (
            "Generate study flashcards from learning material "
            "with SandBox's AI Flashcard Generator."
        ),
    },

    "/youtube-summarizer": {
        "title": (
            "YouTube Summarizer - Summarize Videos | SandBox"
        ),
        "description": (
            "Summarize YouTube videos into concise notes, "
            "key points and takeaways with SandBox."
        ),
    },

    "/regex-gen": {
        "title": (
            "Regex Generator - Build Regular Expressions | SandBox"
        ),
        "description": (
            "Generate regular expressions from plain English "
            "and test pattern ideas faster with SandBox."
        ),
    },

    "/decision-maker": {
        "title": (
            "Decision Maker - Compare Options with AI | SandBox"
        ),
        "description": (
            "Compare choices, risks, pros, cons and recommendations "
            "with SandBox's AI Decision Maker."
        ),
    },

    "/commit-gen": {
        "title": (
            "Commit Message Generator - Write Git Commits | SandBox"
        ),
        "description": (
            "Generate clear Git commit messages from code changes "
            "and development context with SandBox."
        ),
    },

    "/error": {
        "title": (
            "Error Explainer - Debug Error Messages | SandBox"
        ),
        "description": (
            "Paste error messages and get simple explanations, "
            "likely causes and debugging steps with SandBox."
        ),
    },

    "/yaml": {
        "title": (
            "YAML Generator - Create Kubernetes YAML | SandBox"
        ),
        "description": (
            "Generate Kubernetes YAML for deployments, services, "
            "ConfigMaps and related resources with SandBox."
        ),
    },

    "/code": {
        "title": (
            "Code Reviewer - Review Code with AI | SandBox"
        ),
        "description": (
            "Review code for bugs, clarity, security concerns "
            "and improvements with SandBox's AI Code Reviewer."
        ),
    },

    "/docker": {
        "title": (
            "Dockerfile Generator - Create Docker Configs | SandBox"
        ),
        "description": (
            "Generate Dockerfiles and container setup guidance "
            "from project context with SandBox."
        ),
    },

    "/item": {
        "title": (
            "Item Extractor - Extract Structured Items | SandBox"
        ),
        "description": (
            "Extract structured items from uploaded content and "
            "turn unstructured inputs into useful data with SandBox."
        ),
    },

    "/brainstorm-generator": {
        "title": (
            "Brainstorm Generator - Generate Ideas with AI | SandBox"
        ),
        "description": (
            "Brainstorm ideas, angles and creative directions "
            "for projects, writing and planning with SandBox."
        ),
    },
}


# ============================================================
# PRIVATE PAGES
# ============================================================

PRIVATE_PAGES = {
    "/bookmarks_page": "Bookmarks",
    "/forgot-password": "Forgot Password",
    "/history": "History",
    "/login": "Login",
    "/profile": "Profile",
    "/reset-password": "Reset Password",
    "/settings": "Settings",
    "/signup": "Sign Up",
    "/user": "User Panel",
}


# ============================================================
# DEVELOPER ENTITIES
# ============================================================

def nagraj_person_schema() -> dict:
    """
    Main developer identity.

    Keep this information accurate and visible on the
    corresponding profile page.
    """

    return {
        "@type": "Person",
        "@id": NAGRAJ_ID,

        "name": "Nagraj Rangarej",

        "alternateName": [
            "Nikhil Rangarej"
        ],

        "url": absolute_url(
            "/developers/nagraj-rangarej"
        ),

        "image": absolute_url(
            "/assets/developers/nagraj.png"
        ),

        "jobTitle": (
            "AI & Data Science Developer"
        ),

        "description": (
            "Nagraj Rangarej is an AI and Data Science "
            "engineering student and developer focused on "
            "artificial intelligence, software development, "
            "data science and practical AI-powered products. "
            "He is a developer behind SandBox, an AI-powered "
            "software platform that brings practical tools for "
            "developers, students and creators into one workspace."
        ),

        "worksFor": {
            "@id": ORGANIZATION_ID
        },

        "memberOf": {
            "@id": ORGANIZATION_ID
        },

        "knowsAbout": [
            "Artificial Intelligence",
            "Data Science",
            "Machine Learning",
            "Python",
            "Java",
            "SQL",
            "Software Development",
            "AI Tools",
            "AI Applications",
            "Developer Tools",
            "Natural Language Processing",
            "Computer Science"
        ],

        # Add only real public profiles here.
        #
        # Example:
        # "sameAs": [
        #     "https://github.com/YOUR_USERNAME",
        #     "https://www.linkedin.com/in/YOUR_PROFILE/"
        # ]
        #
        "sameAs": [
            "https://github.com/NikDev345"
        ],
    }


def mitansh_person_schema() -> dict:
    """
    Secondary developer identity.

    Only add verified public profile URLs.
    """

    return {
        "@type": "Person",
        "@id": MITANSH_ID,

        "name": "Mitansh Rathi",

        "url": absolute_url(
            "/developers/mitansh-rathi"
        ),

        "description": (
            "Mitansh Rathi is a software and AI developer "
            "working on backend systems, AI-powered developer "
            "tools and product engineering for SandBox."
        ),

        "worksFor": {
            "@id": ORGANIZATION_ID
        },

        "memberOf": {
            "@id": ORGANIZATION_ID
        },

        "knowsAbout": [
            "Backend Development",
            "FastAPI",
            "SQLAlchemy",
            "PostgreSQL",
            "Artificial Intelligence",
            "Machine Learning",
            "AI Systems",
            "Developer Tools",
            "API Development",
            "Software Engineering",
            "Automation",
            "Product Engineering"
        ],

        # DO NOT invent URLs.
        # Add verified GitHub / LinkedIn / personal website
        # URLs when available.
        "sameAs": [],
    }


# ============================================================
# ORGANIZATION ENTITY
# ============================================================

def organization_schema() -> dict:
    """
    Defines SandBox as an online software organization.

    Google recommends Organization structured data for
    helping Search understand an organization's identity.
    """

    return {
        "@type": [
            "Organization",
            "OnlineBusiness"
        ],

        "@id": ORGANIZATION_ID,

        "name": SITE_NAME,

        "alternateName": [
            "SandBox AI",
            "SandBox AI Tools"
        ],

        "url": absolute_url("/"),

        "logo": {
            "@type": "ImageObject",
            "url": absolute_url(
                DEFAULT_IMAGE_PATH
            )
        },

        "image": absolute_url(
            DEFAULT_IMAGE_PATH
        ),

        "description": (
            "SandBox is an AI-powered software platform "
            "built to provide practical tools for developers, "
            "students and creators. The platform brings "
            "AI-powered productivity, developer, learning, "
            "content and data-processing tools into one "
            "online workspace."
        ),

        "knowsAbout": [
            "Artificial Intelligence",
            "AI Software",
            "AI Productivity Tools",
            "Developer Tools",
            "Software Development",
            "Machine Learning",
            "Data Science",
            "Automation",
            "Education Technology",
            "Developer Productivity"
        ],

        "founder": [
            {
                "@id": NAGRAJ_ID
            },
            {
                "@id": MITANSH_ID
            }
        ],

        "employee": [
            {
                "@id": NAGRAJ_ID
            },
            {
                "@id": MITANSH_ID
            }
        ],

        "creator": [
            {
                "@id": NAGRAJ_ID
            },
            {
                "@id": MITANSH_ID
            }
        ],

        "sameAs": [
            absolute_url("/")
        ],
    }


# ============================================================
# WEBSITE ENTITY
# ============================================================

def website_schema() -> dict:
    return {
        "@type": "WebSite",

        "@id": WEBSITE_ID,

        "name": SITE_NAME,

        "alternateName": [
            "SandBox AI",
            "SandBox AI Tools"
        ],

        "url": absolute_url("/"),

        "description": (
            "SandBox is an AI-powered software platform "
            "providing practical tools for developers, "
            "students and creators."
        ),

        "publisher": {
            "@id": ORGANIZATION_ID
        },

        "creator": {
            "@id": NAGRAJ_ID
        },

        "about": {
            "@id": ORGANIZATION_ID
        },

        "inLanguage": "en-IN",
    }


# ============================================================
# WEB APPLICATION ENTITY
# ============================================================

def application_schema() -> dict:
    return {
        "@type": "WebApplication",

        "@id": APPLICATION_ID,

        "name": SITE_NAME,

        "url": absolute_url("/"),

        "description": (
            "SandBox is a web-based AI software platform "
            "providing AI tools for developers, students "
            "and creators."
        ),

        "applicationCategory": [
            "ProductivityApplication",
            "DeveloperApplication",
            "EducationalApplication"
        ],

        "operatingSystem": "Web",

        "browserRequirements": (
            "Requires a modern web browser with JavaScript enabled."
        ),

        "publisher": {
            "@id": ORGANIZATION_ID
        },

        "creator": {
            "@id": NAGRAJ_ID
        },

        "author": {
            "@id": NAGRAJ_ID
        },

        "isPartOf": {
            "@id": WEBSITE_ID
        }
    }


# ============================================================
# HOMEPAGE ENTITY GRAPH
# ============================================================

def homepage_structured_data() -> dict:
    """
    Main entity graph.

    This is the most important structured-data block on
    the homepage.

    Relationship:

        SandBox Website
              |
              +---- Organization
              |        |
              |        +---- Nagraj Rangarej
              |        |
              |        +---- Mitansh Rathi
              |
              +---- WebApplication
              |
              +---- Creator
                       |
                       +---- Nagraj Rangarej
    """

    return {
        "@context": "https://schema.org",

        "@graph": [
            website_schema(),
            organization_schema(),
            application_schema(),
            nagraj_person_schema(),
            mitansh_person_schema(),
        ]
    }


# ============================================================
# PROFILE PAGE STRUCTURED DATA
# ============================================================

def nagraj_profile_schema() -> dict:
    """
    Google ProfilePage entity for Nagraj.

    This should be placed ONLY on Nagraj's actual
    profile/about page.
    """

    return {
        "@context": "https://schema.org",

        "@type": "ProfilePage",

        "@id": absolute_url(
            "/developers/nagraj-rangarej"
        ),

        "url": absolute_url(
            "/developers/nagraj-rangarej"
        ),

        "name": (
            "Nagraj Rangarej - Developer Profile"
        ),

        "description": (
            "Developer profile of Nagraj Rangarej, "
            "an AI and Data Science engineering student "
            "and developer behind SandBox."
        ),

        "mainEntity": nagraj_person_schema(),

        "isPartOf": {
            "@id": WEBSITE_ID
        }
    }


def mitansh_profile_schema() -> dict:
    """
    Google ProfilePage entity for Mitansh.
    """

    return {
        "@context": "https://schema.org",

        "@type": "ProfilePage",

        "@id": absolute_url(
            "/developers/mitansh-rathi"
        ),

        "url": absolute_url(
            "/developers/mitansh-rathi"
        ),

        "name": (
            "Mitansh Rathi - Developer Profile"
        ),

        "description": (
            "Developer profile of Mitansh Rathi, "
            "a software and AI developer working on "
            "SandBox."
        ),

        "mainEntity": mitansh_person_schema(),

        "isPartOf": {
            "@id": WEBSITE_ID
        }
    }


# ============================================================
# ABOUT PAGE STRUCTURED DATA
# ============================================================

def about_page_schema() -> dict:
    return {
        "@context": "https://schema.org",

        "@type": "AboutPage",

        "@id": absolute_url("/about"),

        "url": absolute_url("/about"),

        "name": (
            "About SandBox - AI Platform Built by Developers"
        ),

        "description": (
            "Learn about SandBox and the developers behind "
            "its AI-powered software tools."
        ),

        "isPartOf": {
            "@id": WEBSITE_ID
        },

        "about": {
            "@id": ORGANIZATION_ID
        },

        "mainEntity": {
            "@id": ORGANIZATION_ID
        }
    }


# ============================================================
# PAGE SEO
# ============================================================

def add_page_seo(path: str) -> None:

    if path not in PUBLIC_PAGES:
        return

    metadata = PUBLIC_PAGES[path]

    url = absolute_url(path)

    if path == "/developers/nagraj-rangarej":
        image = absolute_url(
            "/assets/developers/nagraj.png"
        )
    else:
        image = absolute_url(
            DEFAULT_IMAGE_PATH
        )

    head_tags = [

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        _tag(
            "meta",
            {
                "name": "description",
                "content": metadata["description"],
            },
        ),

        # ----------------------------------------------------
        # ROBOTS
        # ----------------------------------------------------

        _tag(
            "meta",
            {
                "name": "robots",
                "content": (
                    "index,follow,"
                    "max-image-preview:large,"
                    "max-snippet:-1,"
                    "max-video-preview:-1"
                ),
            },
        ),

        # ----------------------------------------------------
        # CANONICAL
        # ----------------------------------------------------

        _tag(
            "link",
            {
                "rel": "canonical",
                "href": url,
            },
        ),

        # ----------------------------------------------------
        # OPEN GRAPH
        # ----------------------------------------------------

        _tag(
            "meta",
            {
                "property": "og:type",
                "content": (
                    "profile"
                    if path.startswith("/developers/")
                    else "website"
                ),
            },
        ),

        _tag(
            "meta",
            {
                "property": "og:title",
                "content": metadata["title"],
            },
        ),

        _tag(
            "meta",
            {
                "property": "og:description",
                "content": metadata["description"],
            },
        ),

        _tag(
            "meta",
            {
                "property": "og:url",
                "content": url,
            },
        ),

        _tag(
            "meta",
            {
                "property": "og:site_name",
                "content": SITE_NAME,
            },
        ),

        _tag(
            "meta",
            {
                "property": "og:image",
                "content": image,
            },
        ),

        # ----------------------------------------------------
        # TWITTER / X
        # ----------------------------------------------------

        _tag(
            "meta",
            {
                "name": "twitter:card",
                "content": "summary_large_image",
            },
        ),

        _tag(
            "meta",
            {
                "name": "twitter:title",
                "content": metadata["title"],
            },
        ),

        _tag(
            "meta",
            {
                "name": "twitter:description",
                "content": metadata["description"],
            },
        ),

        _tag(
            "meta",
            {
                "name": "twitter:image",
                "content": image,
            },
        ),

        # ----------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------

        _tag(
            "meta",
            {
                "http-equiv": "content-language",
                "content": "en-IN",
            },
        ),
    ]


    # ========================================================
    # STRUCTURED DATA
    # ========================================================

    if path == "/":

        head_tags.append(
            _json_ld(
                homepage_structured_data()
            )
        )


    elif path == "/about":

        head_tags.append(
            _json_ld(
                about_page_schema()
            )
        )

        head_tags.append(
            _json_ld(
                organization_schema()
            )
        )


    elif path == "/developers/nagraj-rangarej":

        head_tags.append(
            _json_ld(
                nagraj_profile_schema()
            )
        )


    elif path == "/developers/mitansh-rathi":

        head_tags.append(
            _json_ld(
                mitansh_profile_schema()
            )
        )


    # ========================================================
    # INSERT INTO HEAD
    # ========================================================

    ui.add_head_html(
        "\n".join(head_tags)
    )


# ============================================================
# PRIVATE PAGE SEO
# ============================================================

def add_private_seo(path: str) -> None:

    ui.add_head_html(
        "\n".join(
            [

                _tag(
                    "meta",
                    {
                        "name": "robots",
                        "content": "noindex,nofollow",
                    },
                ),

                _tag(
                    "link",
                    {
                        "rel": "canonical",
                        "href": absolute_url(path),
                    },
                ),

            ]
        )
    )


# ============================================================
# ROBOTS.TXT
# ============================================================

def robots_txt() -> str:

    return "\n".join(
        [

            "User-agent: *",

            "Allow: /",

            # Keep private/account pages out of crawling.
            "Disallow: /login",
            "Disallow: /signup",
            "Disallow: /settings",
            "Disallow: /profile",
            "Disallow: /user",
            "Disallow: /history",
            "Disallow: /bookmarks_page",
            "Disallow: /forgot-password",
            "Disallow: /reset-password",

            "",

            f"Sitemap: {absolute_url('/sitemap.xml')}",

            "",

        ]
    )


# ============================================================
# SITEMAP
# ============================================================

def sitemap_xml() -> str:

    urls = []

    for path in PUBLIC_PAGES:

        urls.append(
            "  <url>\n"
            f"    <loc>{html.escape(absolute_url(path))}</loc>\n"
            "  </url>"
        )


    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'

        '<urlset '
        'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        + "\n".join(urls)

        + "\n</urlset>\n"
    )
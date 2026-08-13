import time

_APP_START = time.perf_counter()

def startup_time(label):
    print(
        f"[STARTUP] {label}: "
        f"{time.perf_counter() - _APP_START:.2f}s",
        flush=True
    )

startup_time("main.py started")


from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
import warnings
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from app.routes.user import router as user_router
from fastapi.staticfiles import StaticFiles
from app.ui.seo import robots_txt, sitemap_xml

warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()

fast_app = FastAPI()

# ── Middleware (must all be registered before mounts/routers) ──────────────────

fast_app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY")
)

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
        "http://127.0.0.1:8000",
        "https://sandboxhome.online",
        "https://www.sandboxhome.online",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fast_app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static") or path.startswith("/assets"):
        response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    elif path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response

# ── DB & Models ────────────────────────────────────────────────────────────────

from app.models import *
from app.database.engine import *
startup_time("models + database imported")
Base.metadata.create_all(bind=engine)

# ── Routers ────────────────────────────────────────────────────────────────────

from app.api.image_text_extractor.image_text_extractor import router as image_text_extractor_router
from app.api.auth import router as auth_router
from app.api.tools import router as tool_router
from app.api.exec import router as exe_router
from app.api.analytics import router as analytic_router
startup_time("before Google API")
from app.routes.auth import router as google_router
startup_time("after Google API")
from app.api.summarizer.summarizer import router as summarizer_router
startup_time("after Summarizer API")
from app.api.json_fixer.json_fixer import router as json_fixer_router
startup_time("after JSON Fixer API")
from app.api.ELI5.eli5 import router as eli5_router
startup_time("after ELI5 API")
from app.api.sql_generator.sql_generator import router as sql_router
startup_time("after SQL Generator API")
from app.api.ss_explainer.ss_explainer import router as ss_router
startup_time("after SS Explainer API")
from app.api.pro_cons_gen.pro_cons import router as pro_cons_router
from app.api.notes_cleaner.notes_cleaner import router as notes_cleaner_router
from app.api.quiz.quiz_generator import router as quiz_router
from app.api.brainstorm_generator.brainstorm_generator import router as brainstorm_router
from app.api.blog_generator.blog_outline_generator import router as blog_outline_router
from app.api.api_mock.api_mock import router as mock_api_router, public_router as mock_public_router
from app.api.chart_explainer.chart_explainer import router as chart_explainer_router
from app.api.email_rewriter.email_rewriter import router as email_rewriter_router
from app.api.table_extractor.table_extractor import router as table_extractor_router
from app.api.youtube_summarizer.youtube_summarizer import router as youtube_summarizer_router
from app.api.regex_generator.regex import router as regex_router
from app.api.yaml_generator.yaml import router as yaml_router
from app.api.history import router as history_router
from app.api.decision_maker.decision_maker import router as decision_maker_router
from app.api.commit_message.commit import router as commit_router
from app.api.workspace import router as workspace_router
from app.api.flashcard_generator.flashcard_generator import router as flashcard_generator_router
from app.api.error_explainer.error_explainer import router as error_router
from app.api.code_reviewer.code_reviewer import router as code_router
from app.api.docker_generator.docker_generator import router as docker_router
from app.api.item_extractor.item import router as item_router
from app.api.bookmarks import router as bookmark_router
from app.routes.user import router as user_router
from app.seed.seed_tools import seed_tools
from app.database.engine import SessionLocal
from app.api.admin import router as admin_router
from nicegui import ui
startup_time("all API routers imported")
# ── Static files ───────────────────────────────────────────────────────────────

fast_app.mount("/static", StaticFiles(directory="static"), name="static")

# ── SEO routes ─────────────────────────────────────────────────────────────────

@fast_app.get("/robots.txt", include_in_schema=False)
def get_robots_txt():
    return Response(content=robots_txt(), media_type="text/plain; charset=utf-8")

@fast_app.get("/sitemap.xml", include_in_schema=False)
def get_sitemap_xml():
    return Response(content=sitemap_xml(), media_type="application/xml; charset=utf-8")

# ── Include all routers ────────────────────────────────────────────────────────

fast_app.include_router(auth_router)
fast_app.include_router(admin_router)
fast_app.include_router(tool_router)
fast_app.include_router(exe_router)
fast_app.include_router(analytic_router)
fast_app.include_router(history_router)
fast_app.include_router(google_router)
fast_app.include_router(brainstorm_router)
fast_app.include_router(user_router)
fast_app.include_router(mock_api_router)
fast_app.include_router(mock_public_router)
fast_app.include_router(summarizer_router)
fast_app.include_router(json_fixer_router)
fast_app.include_router(image_text_extractor_router)
fast_app.include_router(eli5_router)
fast_app.include_router(sql_router)
fast_app.include_router(ss_router)
fast_app.include_router(notes_cleaner_router)
fast_app.include_router(flashcard_generator_router)
fast_app.include_router(pro_cons_router)
fast_app.include_router(email_rewriter_router)
fast_app.include_router(quiz_router)
fast_app.include_router(decision_maker_router)
fast_app.include_router(youtube_summarizer_router)
fast_app.include_router(blog_outline_router)
fast_app.include_router(chart_explainer_router)
fast_app.include_router(regex_router)
fast_app.include_router(yaml_router)
fast_app.include_router(table_extractor_router)
fast_app.include_router(workspace_router)
fast_app.include_router(commit_router)
fast_app.include_router(error_router)
fast_app.include_router(code_router)
fast_app.include_router(docker_router)
fast_app.include_router(item_router)
fast_app.include_router(bookmark_router)

# ── NiceGUI pages ──────────────────────────────────────────────────────────────

import app.main
startup_time("NiceGUI pages imported")
# ── Run ────────────────────────────────────────────────────────────────────────
startup_time("before ui.run_with")
ui.run_with(
    fast_app,
    title="SandBox",
    mount_path="/",
    favicon="app/ui/assets/logo.png",
    storage_secret=os.getenv("STORAGE_SECRET"),  # ✅ CRITICAL FIX
)
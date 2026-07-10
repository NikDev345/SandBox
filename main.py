from fastapi import FastAPI
from app.models import *
from app.database.engine import *
from fastapi.middleware.cors import CORSMiddleware
import warnings
from app.api.auth import router as auth_router
from app.api.tools import router as tool_router
from app.api.exec import router as exe_router
from app.api.analytics import router as analytic_router
from app.routes.auth import router as google_router
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from app.routes.user import router as user_router

# tools
from app.api.summarizer.summarizer import router as summarizer_router
from app.api.json_fixer.json_fixer import router as json_fixer_router
from app.api.code_reviewer.code_reviewer import router as code_reviewer_router

from nicegui import ui, app
from app.seed.seed_tools import seed_tools
from app.database.engine import SessionLocal

warnings.filterwarnings("ignore", category=UserWarning)
Base.metadata.create_all(bind=engine)   

db = SessionLocal()

try:
    seed_tools(db)
finally:
    db.close()

fastapi_app = FastAPI()
app.add_static_files(
    "/assets",
    "app/ui/assets"
)

load_dotenv()
fastapi_app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY")
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(auth_router)
fastapi_app.include_router(tool_router)
fastapi_app.include_router(exe_router)
fastapi_app.include_router(analytic_router)
fastapi_app.include_router(google_router)
fastapi_app.include_router(user_router)
fastapi_app.include_router(summarizer_router)
fastapi_app.include_router(json_fixer_router)
fastapi_app.include_router(code_reviewer_router)


import app.ui.pages.login
import app.ui.pages.test
import app.ui.pages.signup
import app.ui.pages.dashboard
import app.ui.pages.profile
import app.ui.pages.forgot_password
import app.ui.pages.reset_password
import app.ui.pages.text_summarizer
import app.ui.pages.json_fixer
import app.ui.pages.code_reviewer



ui.run_with(
    fastapi_app,
    title="SandBox",
    mount_path="/",
    favicon='app/ui/assets/logo.png'

)
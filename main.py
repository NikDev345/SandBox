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
<<<<<<< HEAD
from app.api.summarizer.summarizer import router as summarizer_router
=======
from app.api.ai.summarizer import router as summarizer_router
from app.api.json_fixer import router as json_fixer_router
>>>>>>> af64e00f90431fcc7d5e2797cf66d87255a5d41a
import app.main 
from nicegui import ui
from app.seed.seed_tools import seed_tools
from app.database.engine import SessionLocal

warnings.filterwarnings("ignore", category=UserWarning)
Base.metadata.create_all(bind=engine)   

db = SessionLocal()

try:
    seed_tools(db)
finally:
    db.close()

app = FastAPI()

load_dotenv()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY")
)

app.add_middleware(
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

app.include_router(auth_router)
app.include_router(tool_router)
app.include_router(exe_router)
app.include_router(analytic_router)
app.include_router(google_router)
app.include_router(user_router)
app.include_router(summarizer_router)
app.include_router(json_fixer_router)

ui.run_with(
    app,
    title="SandBox",
    mount_path="/",
    favicon='app/ui/assets/logo.png'

)
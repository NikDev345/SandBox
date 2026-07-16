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
from app.api.image_text_extractor.image_text_extractor import router as image_text_extractor_router
# tools
from app.api.summarizer.summarizer import router as summarizer_router
from app.api.json_fixer.json_fixer import router as json_fixer_router
from app.api.code_reviewer.code_reviewer import router as code_reviewer_router
from app.api.ELI5.eli5 import router as eli5_router
from app.api.sql_generator.sql_generator import router as sql_router
from app.api.ss_explainer.ss_explainer import router as ss_router
from app.api.pro_cons_gen.pro_cons import router as pro_cons_router
from app.api.notes_cleaner.notes_cleaner import router as notes_cleaner_router
from app.api.quiz.quiz_generator import router as quiz_router


from app.api.youtube_summarizer.youtube_summarizer import router as youtube_summarizer_router
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
app.include_router(code_reviewer_router)
app.include_router(image_text_extractor_router)
app.include_router(eli5_router)
app.include_router(sql_router)
app.include_router(ss_router)
app.include_router(notes_cleaner_router)

app.include_router(pro_cons_router)

app.include_router(quiz_router)
app.include_router(youtube_summarizer_router)

ui.run_with(
    
    app,
    title="SandBox",
    mount_path="/",
    favicon='app/ui/assets/logo.png'

)
<<<<<<< HEAD
from nicegui import ui, app

app.add_static_files(
    '/assets',
    'app/ui/assets'
)

ui.add_head_html("""
<link rel="stylesheet" href="/assets/css/main.css">
""", shared=True)

ui.add_body_html("""
<script src="/assets/js/main.js"></script>
""", shared=True)

import app.ui.pages.dashboard
import app.ui.pages.login
import app.ui.pages.profile
import app.ui.pages.tool_page

ui.run(
    title='ToolBox',
    dark=True,
    reload=True
)
=======
from fastapi import FastAPI
import models
from models import *
from database.engine import *
from fastapi.middleware.cors import CORSMiddleware
import warnings
from app.api.auth import router as auth_router

warnings.filterwarnings("ignore", category=UserWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
>>>>>>> f35524106c0c9033fcbedecf403e0b0a1bd8764a

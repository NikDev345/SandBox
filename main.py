from fastapi import FastAPI
from app.models import *
from app.database.engine import *
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

app.models.Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
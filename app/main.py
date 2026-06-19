from fastapi import FastAPI
import models
from models import *
from database.engine import *
from fastapi.middleware.cors import CORSMiddleware
import warnings

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

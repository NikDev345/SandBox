from config import DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# If DATABASE_URL is not set (development/local), fallback to a local SQLite file
db_url = DATABASE_URL or os.getenv('DATABASE_URL') or f"sqlite:///./sandbox.db"

engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith('sqlite') else {})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
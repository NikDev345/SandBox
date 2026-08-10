import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

email_api_key = os.getenv('EMAIL_API')
email_from = os.getenv('EMAIL_FROM')
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
]
# remove None / empty
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_KEYS = [
    OPENAI_KEY,
]
OPENAI_KEYS = [k.strip() for k in OPENAI_KEYS if k and k.strip()]
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

email_api_key = os.getenv('EMAIL_API')
email_from = os.getenv('EMAIL_FROM')
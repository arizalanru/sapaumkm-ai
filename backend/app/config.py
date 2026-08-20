import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    database_url = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'glowmart.db').as_posix()}"
    )


settings = Settings()

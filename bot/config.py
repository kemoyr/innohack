import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    DB_PATH: str = os.getenv("DB_PATH", "data/volunteer.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "hackathon-secret-key")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")


settings = Settings()

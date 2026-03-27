import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _resolve_db_path() -> str:
    """Local dev: ./data/volunteer.db under project root. Production: set DB_PATH=/data/volunteer.db."""
    raw = os.getenv("DB_PATH", "").strip()
    if not raw:
        return str(_PROJECT_ROOT / "data" / "volunteer.db")
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str(_PROJECT_ROOT / p)


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    DB_PATH: str = _resolve_db_path()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "hackathon-secret-key")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")


settings = Settings()

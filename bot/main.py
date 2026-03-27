import asyncio
import logging
import os
import sys

# Ensure project root is on sys.path so `bot` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from bot.database import init_db
from bot.api.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def _init_db():
    logger.info("Initializing database...")
    await init_db()


if __name__ == "__main__":
    try:
        asyncio.run(_init_db())
        app = create_app(None)
        port = int(os.environ.get("PORT", "8000"))
        logger.info("Starting site on 0.0.0.0:%s (API + статика)", port)
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)

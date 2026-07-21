import asyncio
import logging
import os
import sys

# Allow running this module as a script (python bot/main.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from aiogram import Bot, Dispatcher

from bot.config import settings
from bot.database import init_db
from bot.api.app import create_app
from bot.handlers import start, volunteer, coordinator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def run_bot(bot: Bot):
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(volunteer.router)
    dp.include_router(coordinator.router)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)


async def run_api(bot: Bot | None):
    app = create_app(bot)
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting site on 0.0.0.0:%s (API + статика)", port)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logger.info("Initializing database...")
    await init_db()

    bot = Bot(token=settings.BOT_TOKEN) if settings.BOT_TOKEN else None
    tasks = [run_api(bot)]
    if bot is not None:
        tasks.append(run_bot(bot))
    else:
        logger.warning("BOT_TOKEN not set — Telegram bot disabled, running API-only")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)

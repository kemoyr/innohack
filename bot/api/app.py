import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from bot.api.routes import auth, volunteers, events, stats, verification, applications


def create_app(bot=None) -> FastAPI:
    app = FastAPI(title="Volunteer+ API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if bot is not None:
        app.state.bot = bot

    app.include_router(auth.router, prefix="/api")
    app.include_router(volunteers.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(verification.router, prefix="/api")
    app.include_router(applications.router, prefix="/api")

    # Serve frontend static files
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app

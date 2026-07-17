from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from bot.api.routes import auth, volunteers, events, stats, verification, applications
from bot.config import settings


def create_app(bot=None) -> FastAPI:
    app = FastAPI(title="Volunteer+ API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.WEBAPP_URL] if settings.WEBAPP_URL else ["*"],
        allow_credentials=False,
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

    # SPA: Vite assets + index.html for any client route (/ratings, /calendar, …)
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        index_html = frontend_dist / "index.html"
        assets_dir = frontend_dist / "assets"
        dist_resolved = frontend_dist.resolve()

        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return Response(status_code=204)

        @app.get("/", include_in_schema=False)
        async def spa_root():
            return FileResponse(index_html)

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str):
            if full_path.startswith("api"):
                raise HTTPException(status_code=404)
            candidate = (frontend_dist / full_path).resolve()
            try:
                candidate.relative_to(dist_resolved)
            except ValueError:
                return FileResponse(index_html)
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_html)

    return app

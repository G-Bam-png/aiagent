import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import SessionLocal, init_db
from .routers import agents, auth, channels, chat, meta
from .seed import seed_demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()


@app.middleware("http")
async def no_cache_assets(request, call_next):
    """Serve HTML/JS/CSS without caching so iterative UI changes always show up."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "provider": settings.resolved_provider}


# API routers (registered before the catch-all static mount)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(channels.router)
app.include_router(chat.router)
app.include_router(meta.router)

# Serve the frontend (landing, dashboard, embeddable widget) from /
_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")

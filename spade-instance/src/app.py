from __future__ import annotations

from fastapi import FastAPI

from src.routers import router


def get_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app

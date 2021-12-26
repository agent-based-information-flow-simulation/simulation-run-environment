from __future__ import annotations

from aasm.utils.exception import PanicException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.exceptions import handle_panic_exception
from src.routers import router
from src.settings import app_settings


def get_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[app_settings.client_cors_domain],
        allow_methods=["POST"],
    )
    app.add_exception_handler(PanicException, handle_panic_exception)
    return app

from __future__ import annotations

from aasm.utils.exception import PanicException
from fastapi import FastAPI

from src.exceptions import handle_panic_exception
from src.routers import router


def get_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(PanicException, handle_panic_exception)
    return app

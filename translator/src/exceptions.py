from __future__ import annotations

from typing import TYPE_CHECKING

from aasm import __version__
from starlette.responses import JSONResponse

if TYPE_CHECKING:  # pragma: no cover
    from aasm import PanicException
    from starlette.requests import Request


async def handle_panic_exception(request: Request, exception: PanicException):
    return JSONResponse(
        status_code=400,
        content={
            "translator_version": __version__,
            "place": exception.place,
            "reason": exception.reason,
            "suggestion": exception.suggestion,
        },
    )

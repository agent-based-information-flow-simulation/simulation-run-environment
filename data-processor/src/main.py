from __future__ import annotations

import uvicorn

from src.app import get_app
from src.settings import app_settings

app = get_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=app_settings.port,
        reload=app_settings.enable_reload,
    )

from __future__ import annotations

import os

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


app_settings = AppSettings()

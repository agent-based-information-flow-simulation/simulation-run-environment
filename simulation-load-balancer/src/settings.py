from __future__ import annotations

import os

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


class DatabaseSettings(BaseSettings):
    url: str = os.environ.get("DB_URL", "")


app_settings = AppSettings()
database_settings = DatabaseSettings()

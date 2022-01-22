from __future__ import annotations

from typing import List

import orjson
from pydantic import BaseModel


class CreateAgent(BaseModel):
    jid: str
    type: str
    connections: List[str]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps


class Statistics(BaseModel):
    labels: List[str]
    data: List[float]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps

from __future__ import annotations

from typing import Dict, List, Union

import orjson
from pydantic import BaseModel


class UpdateAgent(BaseModel):
    jid: str
    type: str
    floats: Dict[str, float]
    enums: Dict[str, str]
    connections: Dict[str, List[str]]
    messages: Dict[str, List[Dict[str, Union[float, str]]]]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps


class CreateAgent(BaseModel):
    jid: str
    type: str
    connections: List[str]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps

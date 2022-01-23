from __future__ import annotations

from typing import List

import orjson
from pydantic import BaseModel, validator


class CreateAgent(BaseModel):
    jid: str
    type: str
    connections: List[str]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps


class Statistics(BaseModel):
    data: List[float]
    labels: List[str]

    @validator("labels")
    def labels_and_data_must_have_the_same_length(cls, value, values):
        if len(value) != len(values["data"]):
            raise ValueError("labels and data must have the same length")
        return value

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson.dumps

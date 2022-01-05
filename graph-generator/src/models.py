from __future__ import annotations

from typing import List

from pydantic import BaseModel


class PythonCode(BaseModel):
    graph_code_lines: List[str]

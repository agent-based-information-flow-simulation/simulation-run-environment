from __future__ import annotations

from typing import List

from pydantic import BaseModel


class PythonCode(BaseModel):
    agent_code_lines: List[str]
    graph_code_lines: List[str]

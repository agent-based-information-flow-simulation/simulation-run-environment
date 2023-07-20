from __future__ import annotations

from typing import List

from pydantic import BaseModel


class AgentsAssemblyCode(BaseModel):
    code_lines: List[str]
    module_lines: List[List[str]]



class PythonSpadeCode(BaseModel):
    agent_code_lines: List[str]
    graph_code_lines: List[str]
    module_code_lines: List[str]

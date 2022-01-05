from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class CreateSimulation(BaseModel):
    agent_code_lines: List[str]
    agent_data: List[Dict[str, Any]]

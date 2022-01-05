from __future__ import annotations

from aasm import __version__, get_spade_code
from fastapi import APIRouter

from src.models import AgentsAssemblyCode, PythonSpadeCode

router = APIRouter()


@router.post("/python/spade", response_model=PythonSpadeCode, status_code=200)
async def translate_aasm(agent_assembly_code: AgentsAssemblyCode):
    spade_code = get_spade_code(agent_assembly_code.code_lines)
    return PythonSpadeCode(
        agent_code_lines=spade_code.agent_code_lines,
        graph_code_lines=spade_code.graph_code_lines,
    )

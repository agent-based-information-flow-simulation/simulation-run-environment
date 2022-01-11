from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from src.dependencies import agent_service
from src.services import AgentService

router = APIRouter()

@router.post("/agents")
async def create_agent(body: Dict[str, Any], agent_service: AgentService = Depends(agent_service)):
    await agent_service.insert_agent("123", body)


@router.get("/agents")
async def get_agents(agent_service: AgentService = Depends(agent_service)):
    return await agent_service.get_agents("123")

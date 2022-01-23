from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from src.dependencies import statistics_service
from src.exceptions import (
    AgentTypeDoesNotExistException,
    InconsistentListDataTypesException,
    InvalidAgentTypeStatisticsRequestException,
    InvalidMessageTypeStatisticsRequestException,
    MessageTypeDoesNotExistException,
    SimulationBackupDoesNotExistException,
)
from src.models import Statistics
from src.services.statistics import StatisticsService

router = APIRouter(prefix="/simulations", default_response_class=ORJSONResponse)


@router.get(
    "/{simulation_id}/statistics/agents/{agent_type}", response_model=Statistics
)
async def get_agent_type_statistics(
    simulation_id: str,
    agent_type: str,
    property: Optional[str] = None,
    message_list: Optional[str] = None,
    message_type: Optional[str] = None,
    connection_list: Optional[str] = None,
    statistics_service: StatisticsService = Depends(statistics_service),
):
    try:
        return await statistics_service.get_agent_type_statistics(
            simulation_id,
            agent_type,
            property,
            message_list,
            message_type,
            connection_list,
        )
    except SimulationBackupDoesNotExistException as e:
        raise HTTPException(400, str(e))
    except AgentTypeDoesNotExistException as e:
        raise HTTPException(400, str(e))
    except InvalidAgentTypeStatisticsRequestException as e:
        raise HTTPException(400, str(e))
    except InconsistentListDataTypesException as e:
        raise HTTPException(500, str(e))


@router.get(
    "/{simulation_id}/statistics/messages/{message_type}", response_model=Statistics
)
async def get_message_type_statistics(
    simulation_id: str,
    message_type: str,
    property: str,
    statistics_service: StatisticsService = Depends(statistics_service),
):
    try:
        return await statistics_service.get_message_type_statistics(
            simulation_id,
            message_type,
            property,
        )
    except SimulationBackupDoesNotExistException as e:
        raise HTTPException(400, str(e))
    except MessageTypeDoesNotExistException as e:
        raise HTTPException(400, str(e))
    except InvalidMessageTypeStatisticsRequestException as e:
        raise HTTPException(400, str(e))
    except InconsistentListDataTypesException as e:
        raise HTTPException(500, str(e))

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from src.dependencies import timeseries_service
from src.exceptions import TimeseriesDoesNotExistException
from src.services.timeseries import TimeseriesService

router = APIRouter(prefix="/simulations", default_response_class=ORJSONResponse)


@router.get("/{simulation_id}/timeseries")
async def get_timeseries(
    simulation_id: str,
    timeseries_service: TimeseriesService = Depends(timeseries_service),
):
    try:
        return await timeseries_service.get_timeseries(simulation_id)
    except TimeseriesDoesNotExistException as e:
        raise HTTPException(400, str(e))


@router.delete("/{simulation_id}/timeseries")
async def delete_timeseries(
    simulation_id: str,
    timeseries_service: TimeseriesService = Depends(timeseries_service),
):
    try:
        return await timeseries_service.delete_timeseries(simulation_id)
    except TimeseriesDoesNotExistException as e:
        raise HTTPException(400, str(e))

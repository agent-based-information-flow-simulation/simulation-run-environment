from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException

import httpx
import logging
from aioredis import Redis
import json
from typing import Optional, Any
from src.dependencies import graph_generator_service, translator_service, redis, simulation_creator_service
from src.exceptions import GraphGeneratorException, TranslatorException, SimulationCreatorException
from src.models import CreatedSimulation, CreateSpadeSimulation, InstanceState, InstanceData, \
    SimulationLoadBalancerState
from src.services.graph_generator import GraphGeneratorService
from src.services.simulation_creator import SimulationCreatorService
from src.services.translator import TranslatorService
from src.status import Status

router = APIRouter()


@router.get("/simulations/", response_model=SimulationLoadBalancerState, status_code=200)
async def get_instance_states(
        redis_conn: Redis = Depends(redis)
):
    instances = []
    async for key in redis_conn.scan_iter():
        instance = await redis_conn.get(key)
        instance = json.loads(instance)
        instance_id = key.decode("UTF-8")
        data = InstanceData(key=instance_id, status=instance["status"], simulation_id=instance["simulation_id"], num_agents=instance["num_agents"],
                            broken_agents=instance["broken_agents"],
                            api_memory_usage_MiB=instance["api_memory_usage_MiB"],
                            simulation_memory_usage_MiB=instance["simulation_memory_usage_MiB"])
        instances.append(data)
    return SimulationLoadBalancerState(instances=instances)


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def create_simulation(
        simulation_data: CreateSpadeSimulation,
        translator_service: TranslatorService = Depends(translator_service),
        graph_generator_service: GraphGeneratorService = Depends(graph_generator_service),
        simulation_creator_service: SimulationCreatorService = Depends(simulation_creator_service),
        redis_conn: Redis = Depends(redis)
):
    logging.error("GOT CREATE REQUEST WEEEEE!")
    try:
        agent_code_lines, graph_code_lines = await translator_service.translate(
            simulation_data.aasm_code_lines
        )
    except TranslatorException as e:
        raise HTTPException(500, f"Could not create a simulation (translator: {e}).")

    try:
        graph = await graph_generator_service.generate(graph_code_lines)
    except GraphGeneratorException as e:
        raise HTTPException(
            500, f"Could not create a simulation (graph generator: {e})."
        )

    # start the simulation
    available_instances = []
    # get every instance which is available
    async for key in redis_conn.scan_iter():
        instance = await redis_conn.get(key)
        instance = json.loads(instance)
        instance["key"] = key.decode("UTF-8");
        logging.warning(instance["key"])
        if str(instance["status"]) == Status.IDLE.name:
            available_instances.append(instance)
    logging.warning(f"Found {len(available_instances)} instances")
    logging.warning(f"graph contains {len(graph)} agent definitions")

    try:
        logging.info("Creating simulation...")
        sim_id = await simulation_creator_service.create(agent_code_lines, graph, available_instances)
    except SimulationCreatorException as e:
        logging.error(f"{e}")
        raise HTTPException(
            500, f"Couldn't create simulation (spade instance:{e})"
        )

    return {"simulation_id": "3", "info": "reee"}


@router.put("/instances/{instance_id}/state", status_code=200)
async def save_instance_data(
        instance_id: str,
        body: InstanceState,
        redis_conn: Redis = Depends(redis),
):
    logging.warning(f"Got state from instance: {instance_id}. State is: {body.json()}")
    await redis_conn.mset({instance_id: body.json()});
    return


@router.delete("/simulations/{simulation_id}", status_code=200)
async def del_instance_Data(
        simulation_id: str,
):
    url = f"http://{instance_id}:8000"
    async with httpx.AsyncClient(base_url=url) as client:
        response = await client.delete("/simulation")
        if (response.status_code != 200):
            print("XD")

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException

import httpx
import logging
from aioredis import Redis
import json
from typing import Optional, Any
from src.dependencies import graph_generator_service, translator_service, redis, simulation_creator_service, \
    data_processor_service
from src.exceptions import GraphGeneratorException, TranslatorException, SimulationCreatorException, \
    DataProcessorException
from src.models import CreatedSimulation, CreateSpadeSimulation, InstanceState, InstanceData, \
    SimulationLoadBalancerState
from src.services.graph_generator import GraphGeneratorService
from src.services.simulation_creator import SimulationCreatorService
from src.services.translator import TranslatorService
from src.services.data_processor import DataProcessorService
from src.status import Status

from uuid import uuid4

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
        data = InstanceData(key=instance_id, status=instance["status"], simulation_id=instance["simulation_id"],
                            num_agents=instance["num_agents"],
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
        data_processor_service: DataProcessorService = Depends(data_processor_service),
        redis_conn: Redis = Depends(redis)
):
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

    simulation_id = str(uuid4())[:10]
    try:
        backup_status = await data_processor_service.save_state(simulation_id, graph)
    except DataProcessorException as e:
        raise HTTPException(
            500, f"Could not create a simulation (data processor: {e})"
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

    try:
        logging.info("Creating simulation...")
        attempt = 1
        success = False
        # attempt three times to create the simulation
        while not success and attempt <= 3:
            attempt = attempt + 1
            bad_instances = await simulation_creator_service.create(agent_code_lines, graph, available_instances,
                                                                    simulation_id)
            if len(bad_instances) == 0:
                # if every instance successfully started we finish
                success = True
            else:
                # otherwise, we check the health of all instances, to see if they are still up
                bad_instances = await simulation_creator_service.check_health(bad_instances)
                # these instances must be removed from consideration
                available_instances = [inst for inst in available_instances if inst['key'] not in bad_instances]
                await redis_conn.delete(*bad_instances)
                # for the remaining instances we need to delete all the correctly started simulations
                await simulation_creator_service.delete_simulation_instances(available_instances)
        if not success:
            raise HTTPException(
                500, f"Couldn't create simulation (spade instances failed to start)"
            )
    except SimulationCreatorException as e:
        raise HTTPException(
            500, f"Couldn't create simulation (spade instance:{e})"
        )

    return CreatedSimulation(simulation_id=simulation_id, info="")


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
    url = f"http://{simulation_id}:8000"
    async with httpx.AsyncClient(base_url=url) as client:
        response = await client.delete("/simulation")

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException

import httpx
import logging
from aioredis import Redis
import json
from starlette import status
from typing import Optional, Any
from src.dependencies import graph_generator_service, translator_service, redis, simulation_creator_service, \
    data_processor_service
from src.exceptions import GraphGeneratorException, TranslatorException, SimulationCreatorException, \
    DataProcessorException
from src.models import CreatedSimulation, CreateSpadeSimulation, InstanceState, InstanceData, \
    SimulationLoadBalancerState, SimulationData
from src.services.graph_generator import GraphGeneratorService
from src.services.simulation_creator import SimulationCreatorService
from src.services.translator import TranslatorService
from src.services.data_processor import DataProcessorService
from src.status import Status

from uuid import uuid4

router = APIRouter()


@router.get("/simulations", response_model=SimulationLoadBalancerState, status_code=200)
async def get_states(
        redis_conn: Redis = Depends(redis)
):
    instances = []
    simulations = []
    async for key in redis_conn.scan_iter():
        key_data = await redis_conn.get(key)
        key_data = json.loads(key_data)
        try:
            is_sim = key_data["simulation"]
            if is_sim:
                data = SimulationData(simulation_id= key_data["key"], status=key_data["status"])
                simulations.append(data)
        except KeyError:
            instance = key_data
            instance_id = key.decode("UTF-8")
            data = InstanceData(key=instance_id, status=instance["status"], simulation_id=instance["simulation_id"],
                                num_agents=instance["num_agents"],
                                broken_agents=instance["broken_agents"],
                                api_memory_usage_MiB=instance["api_memory_usage_MiB"],
                                simulation_memory_usage_MiB=instance["simulation_memory_usage_MiB"])
            instances.append(data)
    return SimulationLoadBalancerState(instances=instances, simulations=simulations)


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def create_simulation(
        simulation_data: CreateSpadeSimulation,
        translator_service_conn: TranslatorService = Depends(translator_service),
        graph_generator_service_conn: GraphGeneratorService = Depends(graph_generator_service),
        simulation_creator_service_conn: SimulationCreatorService = Depends(simulation_creator_service),
        data_processor_service_conn: DataProcessorService = Depends(data_processor_service),
        redis_conn: Redis = Depends(redis)
):
    try:
        agent_code_lines, graph_code_lines = await translator_service_conn.translate(
            simulation_data.aasm_code_lines
        )
    except TranslatorException as e:
        raise HTTPException(500, f"Could not create a simulation (translator: {e}).")

    try:
        graph = await graph_generator_service_conn.generate(graph_code_lines)
    except GraphGeneratorException as e:
        raise HTTPException(
            500, f"Could not create a simulation (graph generator: {e})."
        )

    simulation_id = str(uuid4())[:10]
    try:
        backup_status = await data_processor_service_conn.save_state(simulation_id, graph)
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
        # TODO MOVE TO ANOTHER FUNCTION
        # attempt three times to create the simulation
        while not success and attempt <= 3:
            attempt = attempt + 1
            bad_instances = await simulation_creator_service_conn.create(agent_code_lines, graph, available_instances,
                                                                         simulation_id)
            if len(bad_instances) == 0:
                # if every instance successfully started we finish
                success = True
            else:
                # otherwise, we check the health of all instances, to see if they are still up
                bad_instances = await simulation_creator_service_conn.check_health(bad_instances)
                bad_instances = filter(
                    lambda instance_error: instance_error['status_code'] == status.HTTP_503_SERVICE_UNAVAILABLE,
                    bad_instances)
                # these instances must be removed from consideration
                bad_keys = [inst['key'] for inst in bad_instances]
                available_instances = [inst for inst in available_instances if inst['key'] not in bad_keys]
                await redis_conn.delete(*bad_keys)
                # for the remaining instances we need to delete all the correctly started simulations
                await simulation_creator_service_conn.delete_simulation_instances(available_instances)
        if not success:
            raise HTTPException(
                500, f"Couldn't create simulation (spade instances failed to start)"
            )
    except SimulationCreatorException as e:
        raise HTTPException(
            500, f"Couldn't create simulation (spade instance:{e})"
        )
    sim_data = {
        "available_instances": available_instances,
        "status": Status.ACTIVE.name,
        "simulation": True,
        "key": simulation_id
    }
    await redis_conn.mset({simulation_id: json.dumps(sim_data)})

    return CreatedSimulation(simulation_id=simulation_id, status=Status.ACTIVE.name, info="")


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
async def del_instance_data(
        simulation_id: str,
        simulation_creator_service_conn: SimulationCreatorService = Depends(simulation_creator_service),
        redis_conn: Redis = Depends(redis)
):
    sim_data = await redis_conn.get(simulation_id)
    sim_instances = []
    if sim_data is None:
        raise HTTPException(
            status_code=500, detail=f"Couldn't delete simulation: No simulation with that id"
        )
    else:
        sim_instances = json.loads(sim_data)

    success = False
    attempt = 0
    to_delete = sim_instances['available_instances']
    while not success and attempt < 3:
        error_instances = await simulation_creator_service_conn.delete_simulation_instances(to_delete)
        if len(error_instances) == 0:
            success = True
        else:
            to_delete = error_instances
            attempt += 1
    if not success:
        new_sim_data = {
            "available_instances": [],
            "status": Status.BROKEN.name,
            "simulation": True,
            "key": simulation_id
        }
        await redis_conn.mset({simulation_id: json.dumps(new_sim_data)})
        raise HTTPException(
            status_code=504, detail=f"Failed to delete simulation at {json.dumps(error_instances)}"
        )
    else:
        new_sim_data = {
            "available_instances": [],
            "status": Status.DEACTIVATED.name,
            "simulation": True,
            "key": simulation_id
        }
        await redis_conn.mset({simulation_id: json.dumps(new_sim_data)})

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from starlette import status

from src.dependencies import state
from src.exceptions import SimulationException
from src.settings import backup_settings
from src.state import State
from src.status import Status

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from pytest_httpx import HTTPXMock

pytestmark = pytest.mark.asyncio


async def test_create_simulation_after_creating_simulaton_response_has_201_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock(spec=State)
    start_simulation_process_future = asyncio.Future()
    start_simulation_process_future.set_result(None)
    state_mock.start_simulation_process.return_value = start_simulation_process_future
    app.dependency_overrides[state] = lambda: state_mock

    data = {"simulation_id": "", "agent_code_lines": [], "agent_data": []}

    response = await client.post("/simulation", json=data)

    assert response.status_code == status.HTTP_201_CREATED


async def test_create_simulation_after_trying_to_create_simulation_if_other_one_is_running_response_has_400_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock(spec=State)
    start_simulation_process_future = asyncio.Future()
    start_simulation_process_future.set_exception(
        SimulationException(Status.RUNNING, "")
    )
    state_mock.start_simulation_process.side_effect = start_simulation_process_future
    app.dependency_overrides[state] = lambda: state_mock

    data = {"simulation_id": "", "agent_code_lines": [], "agent_data": []}

    response = await client.post("/simulation", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_create_simulation_after_trying_to_create_simulation_if_other_one_is_running_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock(spec=State)
    start_simulation_process_future = asyncio.Future()
    start_simulation_process_future.set_exception(
        SimulationException(Status.RUNNING, "")
    )
    state_mock.start_simulation_process.side_effect = start_simulation_process_future
    app.dependency_overrides[state] = lambda: state_mock

    data = {"simulation_id": "", "agent_code_lines": [], "agent_data": []}

    response = await client.post("/simulation", json=data)

    assert "detail" in response.json()


async def test_delete_simulation_after_deleting_simulation_response_has_200_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()

    get_state_future = asyncio.Future()
    get_state_future.set_result((Status.RUNNING, "", 0, []))
    state_mock.get_state.return_value = get_state_future

    kill_simulation_process_future = asyncio.Future()
    kill_simulation_process_future.set_result(None)
    state_mock.kill_simulation_process.return_value = kill_simulation_process_future

    app.dependency_overrides[state] = lambda: state_mock

    response = await client.delete("/simulation")

    assert response.status_code == status.HTTP_200_OK


async def test_delete_simulation_after_deleting_simulation_response_has_simulation_id(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()

    get_state_future = asyncio.Future()
    get_state_future.set_result((Status.RUNNING, "", 0, []))
    state_mock.get_state.return_value = get_state_future

    kill_simulation_process_future = asyncio.Future()
    kill_simulation_process_future.set_result(None)
    state_mock.kill_simulation_process.return_value = kill_simulation_process_future

    app.dependency_overrides[state] = lambda: state_mock

    response = await client.delete("/simulation")

    assert "simulation_id" in response.json()


async def test_delete_simulation_after_simulation_exception_response_has_400_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()

    get_state_future = asyncio.Future()
    get_state_future.set_result((Status.RUNNING, "", 0, []))
    state_mock.get_state.return_value = get_state_future

    kill_simulation_process_future = asyncio.Future()
    kill_simulation_process_future.set_exception(SimulationException(Status.IDLE, ""))
    state_mock.kill_simulation_process.side_effect = kill_simulation_process_future

    app.dependency_overrides[state] = lambda: state_mock

    response = await client.delete("/simulation")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_delete_simulation_after_simulation_exception_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()

    get_state_future = asyncio.Future()
    get_state_future.set_result((Status.RUNNING, "", 0, []))
    state_mock.get_state.return_value = get_state_future

    kill_simulation_process_future = asyncio.Future()
    kill_simulation_process_future.set_exception(SimulationException(Status.IDLE, ""))
    state_mock.kill_simulation_process.side_effect = kill_simulation_process_future

    app.dependency_overrides[state] = lambda: state_mock

    response = await client.delete("/simulation")

    assert "detail" in response.json()


async def test_backup_agent_data_after_sending_data_response_has_201_status_code(
    app: FastAPI, client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{backup_settings.api_backup_url}/simulations/123/data",
        method="PUT",
        status_code=200,
        json={},
    )

    state_mock = Mock()
    get_simulation_id_future = asyncio.Future()
    get_simulation_id_future.set_result("123")
    state_mock.get_simulation_id.return_value = get_simulation_id_future
    app.dependency_overrides[state] = lambda: state_mock

    data = {"jid": "abc"}

    response = await client.post("/internal/simulation/agent_data", json=data)

    assert response.status_code == status.HTTP_201_CREATED


async def test_update_active_instance_status_after_sending_status_response_has_201_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()
    update_active_state_future = asyncio.Future()
    update_active_state_future.set_result(None)
    state_mock.update_active_state.return_value = update_active_state_future
    app.dependency_overrides[state] = lambda: state_mock

    instance_status = {
        "status": Status.RUNNING.name,
        "num_agents": 0,
        "broken_agents": [],
    }

    response = await client.post("/internal/instance/status", json=instance_status)

    assert response.status_code == status.HTTP_201_CREATED


async def test_update_active_instance_status_after_simulation_exception_response_has_400_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()
    update_active_state_future = asyncio.Future()
    update_active_state_future.set_exception(SimulationException(Status.IDLE, ""))
    state_mock.update_active_state.side_effect = update_active_state_future
    app.dependency_overrides[state] = lambda: state_mock

    instance_status = {
        "status": Status.RUNNING.name,
        "num_agents": 0,
        "broken_agents": [],
    }

    response = await client.post("/internal/instance/status", json=instance_status)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_update_active_instance_status_after_simulation_exception_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    state_mock = Mock()
    update_active_state_future = asyncio.Future()
    update_active_state_future.set_exception(SimulationException(Status.IDLE, ""))
    state_mock.update_active_state.side_effect = update_active_state_future
    app.dependency_overrides[state] = lambda: state_mock

    instance_status = {
        "status": Status.RUNNING.name,
        "num_agents": 0,
        "broken_agents": [],
    }

    response = await client.post("/internal/instance/status", json=instance_status)

    assert "detail" in response.json()

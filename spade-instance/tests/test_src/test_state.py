from __future__ import annotations

from multiprocessing import Process
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from src.exceptions import SimulationException, SimulationStateNotSetException
from src.state import get_app_simulation_state, set_app_simulation_state
from src.status import Status

if TYPE_CHECKING:
    from fastapi import FastAPI

    from src.state import State

pytestmark = pytest.mark.asyncio


def test_clean_state_resets_state_to_initial_simulation_values(state: State) -> None:
    state.simulation_process = Mock()
    state.simulation_id = "123"
    state.num_agents = 1
    state.broken_agents = ["agent_1", "agent_2"]

    state._clean_state()

    assert state.simulation_process is None
    assert state.simulation_id is None
    assert state.num_agents == 0
    assert state.broken_agents == []


async def test_update_active_state_updates_running_simulation_values(
    state: State,
) -> None:
    state.status = Status.STARTING
    state.simulation_id = "123"
    state.num_agents = 1
    state.broken_agents = ["agent_1", "agent_2"]

    await state.update_active_state(Status.RUNNING, 2, ["agent_3"])

    assert state.status == Status.RUNNING
    assert state.simulation_id == "123"
    assert state.num_agents == 2
    assert state.broken_agents == ["agent_3"]


async def test_update_active_state_does_not_allow_to_update_idle_simulation(
    state: State,
) -> None:
    state.status = Status.IDLE
    state.simulation_id = "123"
    state.num_agents = 1
    state.broken_agents = ["agent_1", "agent_2"]

    with pytest.raises(SimulationException):
        await state.update_active_state(Status.RUNNING, 2, ["agent_3"])


async def test_get_state_returns_simulation_data(state: State) -> None:
    state.status = Status.IDLE
    state.simulation_id = "123"
    state.num_agents = 1
    state.broken_agents = ["agent_1", "agent_2"]

    state_data = await state.get_state()

    state_data[0] == Status.IDLE
    state_data[1] == "123"
    state_data[2] == 1
    state_data[3] == ["agent_1", "agent_2"]


async def test_get_simulation_id_returns_simulation_id(state: State) -> None:
    state.simulation_id = "123"

    simulation_id = await state.get_simulation_id()

    assert state.simulation_id == simulation_id


@pytest.mark.parametrize("status", [Status.STARTING, Status.RUNNING])
async def test_start_simulation_process_does_not_allow_to_start_simulation_if_another_one_is_active(
    state: State, status: Status
) -> None:
    state.status = status
    simulation_id = "123"
    agent_code_lines = []
    agent_data = []

    with pytest.raises(SimulationException):
        await state.start_simulation_process(
            simulation_id, agent_code_lines, agent_data
        )


@pytest.mark.parametrize("status", [Status.IDLE, Status.DEAD])
async def test_start_simulation_process_allows_to_start_simulation_if_there_is_no_simulation_running(
    state: State, status: Status
) -> None:
    state.status = status
    simulation_id = "123"
    agent_code_lines = []
    agent_data = []

    with patch("src.state.Process"):
        await state.start_simulation_process(
            simulation_id, agent_code_lines, agent_data
        )

    assert state.status == Status.STARTING
    assert state.simulation_id == simulation_id
    assert state.simulation_process is not None


async def test_kill_simulation_process_raises_simulation_exception_if_simulation_process_is_not_set(
    state: State,
) -> None:
    state.simulation_process = None

    with pytest.raises(SimulationException):
        await state.kill_simulation_process()


async def test_kill_simulation_process_sets_status_to_idle(state: State) -> None:
    state.status = Status.RUNNING
    state.simulation_process = Mock(spec=Process)

    await state.kill_simulation_process()

    assert state.status == Status.IDLE


async def test_kill_simulation_process_kills_simulation_process(state: State) -> None:
    state.status = Status.RUNNING
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.kill = Mock()
    state._clean_state = Mock()

    await state.kill_simulation_process()

    assert state.simulation_process.kill.called


async def test_kill_simulation_process_cleans_state(state: State) -> None:
    state.status = Status.RUNNING
    state.simulation_process = Mock(spec=Process)
    state._clean_state = Mock()

    await state.kill_simulation_process()

    assert state._clean_state.called


async def test_get_simulation_memory_usage_returns_0_if_simulation_process_is_not_set(
    state: State,
) -> None:
    state.simulation_process = None

    memory_usage = await state.get_simulation_memory_usage()

    assert memory_usage == 0.0


async def test_get_simulation_memory_usage_returns_0_if_simulation_process_is_not_alive(
    state: State,
) -> None:
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.is_alive.return_value = False

    memory_usage = await state.get_simulation_memory_usage()

    assert memory_usage == 0.0


async def test_get_simulation_memory_usage_returns_usage_in_MiB(state: State) -> None:
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.is_alive.return_value = True
    state.simulation_process.pid = 1

    with patch("psutil.Process.memory_info", return_value=Mock(rss=1024 ** 2)):
        memory_usage = await state.get_simulation_memory_usage()

    assert memory_usage == 1.0


async def test_verify_simulation_process_does_not_change_status_if_process_is_not_set(
    state: State,
) -> None:
    state.status = Status.IDLE
    state.simulation_process = None

    await state.verify_simulation_process()

    assert state.status == Status.IDLE


@pytest.mark.parametrize("status", [Status.STARTING, Status.RUNNING])
async def test_verify_simulation_process_does_not_change_status_if_process_is_alive(
    status: Status, state: State
) -> None:
    state.status = status
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.is_alive.return_value = True

    await state.verify_simulation_process()

    assert state.status == status


async def test_verify_simulation_process_sets_status_to_dead_if_process_is_not_alive(
    state: State,
) -> None:
    state.status = Status.RUNNING
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.is_alive.return_value = False

    await state.verify_simulation_process()

    assert state.status == Status.DEAD


async def test_verify_simulation_process_cleans_state_if_process_is_not_alive(
    state: State,
) -> None:
    state.status = Status.RUNNING
    state.simulation_process = Mock(spec=Process)
    state.simulation_process.is_alive.return_value = False
    state._clean_state = Mock()

    await state.verify_simulation_process()

    assert state._clean_state.called


def test_set_app_simulation_state_sets_simulation_state_inside_app_state(
    app: FastAPI, state: State
) -> None:
    app.state.simulation_state = None

    set_app_simulation_state(app, state)

    assert app.state.simulation_state == state


def test_get_app_simulation_state_returns_simulation_state_from_app_state(
    app: FastAPI, state: State
) -> None:
    app.state.simulation_state = state

    returned_state = get_app_simulation_state(app)

    assert returned_state == state


def test_get_app_simulation_state_raises_simulation_state_not_set_exception_if_simulation_state_is_not_set(
    app: FastAPI,
) -> None:
    with pytest.raises(SimulationStateNotSetException):
        get_app_simulation_state(app)

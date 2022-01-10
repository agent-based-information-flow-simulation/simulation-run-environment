from __future__ import annotations

from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest

from src.simulation.main import SimulationInfiniteLoop, run_simulation

pytestmark = pytest.mark.asyncio


@patch("src.simulation.main.SimulationInfiniteLoop")
@patch("src.simulation.main.Container.reset")
@patch("src.simulation.main.send_status")
@patch("asyncio.sleep")
async def test_simulation_infinite_loop_resets_spade_container(
    mocked_simulation_infinite_loop: Mock,
    mocked_container_reset: Mock,
    mocked_send_status: AsyncMock,
    mocked_sleep: AsyncMock,
) -> None:
    SimulationInfiniteLoop.RUNNING = PropertyMock(side_effect=[True, False])

    agents = []
    agent_num_behaviours = {}
    status_annoucement_period = 0.001
    simulation_infinite_loop = SimulationInfiniteLoop()

    await simulation_infinite_loop.run(
        agents, agent_num_behaviours, status_annoucement_period
    )

    assert mocked_container_reset.called


@patch("src.simulation.main.generate_agents")
@patch("src.simulation.main.connect_agents")
@patch("src.simulation.main.setup_agents")
@patch("src.simulation.main.SimulationInfiniteLoop.run")
async def test_run_simulation(
    mocked_generate_agent: Mock,
    mocked_connect_agents: AsyncMock,
    mocked_setup_agents: Mock,
    mocked_simulation_infinite_loop_run: AsyncMock,
) -> None:
    agent_code_lines = []
    agent_data = []

    await run_simulation(agent_code_lines, agent_data)

    assert mocked_generate_agent.called
    assert mocked_connect_agents.called
    assert mocked_setup_agents.called

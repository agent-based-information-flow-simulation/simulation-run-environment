from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

from src.simulation.initialization import (
    connect_agents,
    connect_with_retry,
    setup_agent,
    setup_agents,
)

pytestmark = pytest.mark.asyncio


@patch("src.simulation.initialization.async_connect")
async def test_connect_with_retry_retries_after_exception(
    async_connect_mock: AsyncMock,
) -> None:
    async_connect_mock.side_effect = [Exception, None]

    agent = Mock(spec=Agent)
    agent.jid = "test@test.com"

    await connect_with_retry(agent, 0.001)

    assert async_connect_mock.call_count == 2


@patch("src.simulation.initialization.connect_with_retry")
async def test_connect_agents(connect_with_retry: AsyncMock) -> None:
    agent1 = Mock(spec=Agent)
    agent1.jid = "test1@test.com"
    agent2 = Mock(spec=Agent)
    agent2.jid = "test2@test.com"
    agents = [agent1, agent2]

    await connect_agents(agents)

    assert connect_with_retry.call_count == 2


async def test_setup_agent_returns_list_of_agent_behaviours() -> None:
    agent = Mock(spec=Agent)
    agent.jid = "test@server.com"
    agent.setup = Mock()
    agent._alive = Mock()
    agent._alive.set = Mock()
    behaviour = Mock(spec=OneShotBehaviour)
    behaviour.is_running = Mock()
    behaviour.is_running.return_value = False
    behaviour.set_agent = Mock()
    behaviour.start = Mock()
    agent.behaviours = [behaviour]

    behaviours = setup_agent(agent)
    
    print(behaviours)

    assert behaviours == agent.behaviours


@patch("src.simulation.initialization.setup_agent")
async def test_setup_agents_returns_dictionary_with_jids_mapped_to_list_of_behaviours(
    setup_agent: Mock,
) -> None:    
    agent = Mock(spec=Agent)
    agent.jid = "agent@test.com"
    behaviour = Mock(spec=OneShotBehaviour)
    behaviour.is_running = Mock()
    behaviour.is_running.return_value = False
    behaviour.set_agent = Mock()
    behaviour.start = Mock()
    agent.behaviours = [behaviour]
    agents = [agent]
    setup_agent.return_value = [behaviour]

    agent_behaviours = setup_agents(agents)

    assert agent_behaviours == {"agent@test.com": [behaviour]}

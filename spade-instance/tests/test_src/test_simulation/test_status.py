from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from spade.agent import Agent

from src.simulation.status import get_broken_agents, get_instance_status, send_status
from src.status import Status

pytestmark = pytest.mark.asyncio


def test_get_broken_agents_returns_empty_list_if_no_agents_are_broken() -> None:
    agents = []
    agent_num_behaviours = {}

    broken_agents = get_broken_agents(agents, agent_num_behaviours)

    assert broken_agents == []


def test_get_broken_agents_returns_list_of_agents_that_are_not_alive() -> None:
    agent = Mock(spec=Agent)
    agent.jid = "agent@test.com"
    agent.is_alive = Mock()
    agent.is_alive.return_value = False
    agents = [agent]
    agent_behaviours = {}

    broken_agents = get_broken_agents(agents, agent_behaviours)

    assert len(broken_agents) == 1


def test_get_broken_agents_returns_empty_list_if_all_behaviours_are_healthy() -> None:
    agent = Mock(spec=Agent)
    agent.jid = "agent@test.com"
    agent.is_alive = Mock()
    agent.is_alive.return_value = True
    b1 = Mock()
    b1._exit_code = 0
    b2 = Mock()
    b2._exit_code = 0
    agent.behaviours = [b1, b2]
    agents = [agent]
    agent_behaviours = {"agent@test.com": [b1, b2]}

    broken_agents = get_broken_agents(agents, agent_behaviours)

    assert len(broken_agents) == 0


def test_get_broken_agents_returns_list_of_agents_for_which_some_of_behaviours_are_broken() -> None:
    agent = Mock(spec=Agent)
    agent.jid = "agent@test.com"
    agent.is_alive = Mock()
    agent.is_alive.return_value = True
    b1 = Mock()
    b1._exit_code = 1
    b2 = Mock()
    b2._exit_code = 0
    agent.behaviours = [b1, b2]
    agents = [agent]
    agent_behaviours = {"agent@test.com": [b1, b2]}

    broken_agents = get_broken_agents(agents, agent_behaviours)

    assert len(broken_agents) == 1


def test_get_broken_agents_returns_list_of_jids() -> None:
    agent = Mock(spec=Agent)
    agent.jid = "agent@test.com"
    agent.is_alive = Mock()
    agent.is_alive.return_value = False
    agents = [agent]
    agent_num_behaviours = []

    broken_agents = get_broken_agents(agents, agent_num_behaviours)

    assert broken_agents == ["agent@test.com"]


def test_get_instance_status_contains_details() -> None:
    num_agents = 2
    broken_agents = ["agent@test.com"]

    status = get_instance_status(num_agents, broken_agents)

    assert status["status"] == Status.RUNNING.name
    assert status["num_agents"] == num_agents
    assert status["broken_agents"] == broken_agents


@patch("httpx.AsyncClient.post")
async def test_send_status_sends_post_request(mocked_post: AsyncMock) -> None:
    agents = []
    agent_num_behaviours = {}

    await send_status(agents, agent_num_behaviours)

    assert mocked_post.called

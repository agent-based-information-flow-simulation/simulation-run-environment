from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock

import pytest

from src.repeated_tasks import (
    create_instance_state_handler,
    create_simulation_process_health_check_handler,
    get_instance_information,
)
from src.state import State, set_app_simulation_state

if TYPE_CHECKING:
    from fastapi import FastAPI
    from pytest_httpx import HTTPXMock


pytestmark = pytest.mark.asyncio


async def test_get_instance_information_returns_instance_details(app: FastAPI) -> None:
    set_app_simulation_state(app, State())

    details = await get_instance_information(app)

    assert "status" in details
    assert "simulation_id" in details
    assert "num_agents" in details
    assert "broken_agents" in details
    assert "api_memory_usage_MiB" in details
    assert "simulation_memory_usage_MiB" in details


async def test_instance_state_handler_is_wrapped_with_repeat_every_decorator(
    app: FastAPI,
) -> None:
    set_app_simulation_state(app, State())

    instance_state_handler = create_instance_state_handler(app)

    assert "__wrapped__" in instance_state_handler.__dict__


async def test_instance_state_handler_after_exception_is_raised_while_sending_state_it_does_not_raise_exception(
    app: FastAPI, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_exception(Exception())
    set_app_simulation_state(app, State())

    instance_state_handler = create_instance_state_handler(app).__wrapped__

    with does_not_raise():
        await instance_state_handler()


async def test_simulation_process_health_check_handler_is_wrapped_with_repeat_every_decorator(
    app: FastAPI,
) -> None:
    set_app_simulation_state(app, State())

    simulation_process_health_check_handler = (
        create_simulation_process_health_check_handler(app)
    )

    assert "__wrapped__" in simulation_process_health_check_handler.__dict__


async def test_simulation_process_health_check_handler_calls_simulation_process_verification(
    app: FastAPI,
) -> None:
    mocked_state = Mock(spec=State)
    mocked_state.verify_simulation_process = AsyncMock()
    set_app_simulation_state(app, mocked_state)

    simulation_process_health_check_handler = (
        create_simulation_process_health_check_handler(app)
    ).__wrapped__

    await simulation_process_health_check_handler()

    assert mocked_state.verify_simulation_process.called

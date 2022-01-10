from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from starlette.requests import Request

from src.dependencies import create_get_simulation_state
from src.state import State, set_app_simulation_state

if TYPE_CHECKING:
    from fastapi import FastAPI


pytestmark = pytest.mark.asyncio


def test_get_simulation_state_returns_simulation_state(app: FastAPI) -> None:
    mocked_state = Mock(spec=State)
    set_app_simulation_state(app, mocked_state)
    mocked_request = Mock(spec=Request)
    mocked_request.app = app
    get_simulation_state = create_get_simulation_state()

    state = get_simulation_state(mocked_request)

    assert state == mocked_state

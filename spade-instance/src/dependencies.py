from __future__ import annotations

from typing import Callable

from starlette.requests import Request

from src.state import State, get_app_simulation_state


def create_get_simulation_state() -> Callable[[Request], State]:
    def get_simulation_state(request: Request) -> State:
        return get_app_simulation_state(request.app)

    return get_simulation_state


state: Callable[[Request], State] = create_get_simulation_state()

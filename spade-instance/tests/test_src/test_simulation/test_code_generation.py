from __future__ import annotations

import pytest

from src.simulation.code_generation import generate_agents, remove_imports

pytestmark = pytest.mark.asyncio


def test_remove_imports_removes_only_import_statements() -> None:
    code = ["import abc", "test", "import xyz"]

    without_imports = remove_imports(code)

    assert without_imports == ["test"]


def test_remove_imports_correctly_handles_empty_code() -> None:
    code = []

    without_imports = remove_imports(code)

    assert without_imports == []


def test_generate_agents_returns_list_of_generated_agents() -> None:
    agent_code_lines = [
        "class first:\n",
        "    def __init__(self, **kwargs):\n",
        "        pass\n",
        "class second:\n",
        "    def __init__(self, **kwargs):\n",
        "        pass\n",
    ]
    agent_data = [{"type": "first"}, {"type": "second"}]

    agents = generate_agents(agent_code_lines, agent_data)

    assert agents[0].__class__.__name__ == "first"
    assert agents[1].__class__.__name__ == "second"

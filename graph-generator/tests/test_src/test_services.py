from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.services import GraphRunnerService

pytestmark = pytest.mark.asyncio


async def test_after_providing_empty_code_method_run_algorithm_returns_empty_graph(
    graph_runner_service: GraphRunnerService,
) -> None:
    code_lines = []

    graph = graph_runner_service.run_algorithm(code_lines)

    assert graph == []


async def test_after_providing_non_empty_code_method_run_algorithm_returns_graph(
    graph_runner_service: GraphRunnerService,
) -> None:
    code_lines = [
        "def generate_graph_structure(domain):\n",
        "    return [{'test': 123}]",
    ]

    graph = graph_runner_service.run_algorithm(code_lines)

    assert graph == [{"test": 123}]


async def test_after_providing_code_with_imports_method_remove_returns_code_without_imports(
    graph_runner_service: GraphRunnerService,
) -> None:
    code_lines = ["import test0\n", "123\n", "import test1\n"]

    graph = graph_runner_service.remove_imports(code_lines)

    assert graph == ["123\n"]


async def test_after_providing_code_without_imports_method_remove_returns_unchanged_code(
    graph_runner_service: GraphRunnerService,
) -> None:
    code_lines = ["123"]

    graph = graph_runner_service.remove_imports(code_lines)

    assert graph == ["123"]

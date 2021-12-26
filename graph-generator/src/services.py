from __future__ import annotations

import random
import uuid
from typing import Any, Callable, Dict, List

import numpy

from src.settings import communication_server_settings


class BaseService:
    ...


class GraphRunnerService(BaseService):
    def run_algorithm(self, graph_code_lines: List[str]) -> List[Dict[str, Any]]:
        code_without_imports = self.remove_imports(graph_code_lines)
        exec("\n".join(code_without_imports))
        try:
            algorithm: Callable[[str], List[Dict[str, Any]]] = locals()[
                "generate_graph_structure"
            ]
        except KeyError:
            return []
        return algorithm(communication_server_settings.domain)

    def remove_imports(self, graph_code_lines: List[str]) -> List[str]:
        return list(
            filter(lambda line: not line.startswith("import"), graph_code_lines)
        )

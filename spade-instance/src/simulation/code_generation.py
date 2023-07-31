from __future__ import annotations

import copy
import datetime
import logging
import os
import importlib.machinery
import types
import random
import sys
from typing import TYPE_CHECKING, Any, Dict, List

import httpx
import numpy
import orjson
import spade

from src.settings import backup_settings, communication_server_settings

if TYPE_CHECKING:  # pragma: no cover
    from aioprocessing import AioQueue
    from spade.agent import Agent

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION_CODE_GENERATION", "INFO"))


def remove_imports(agent_code_lines: List[str]) -> List[str]:
    return list(filter(lambda line: not line.startswith("import"), agent_code_lines))

class Module:
    def __init__(self, name: str):
        self.name = name
        self.code = []
        self.imports = []

    def get_spec(self):
        return importlib.machinery.ModuleSpec(self.name,None)

    def import_code(self):
        module = types.ModuleType(self.name)
        exec("\n".join(self.code), module.__dict__)
        return module

def parse_module_code(module_code_lines: List[str]) -> List[Module]:
    modules = []
    current_module = None
    for line in module_code_lines:
        if line.startswith("# Module: "):
            name = line.split("# Module: ")[1].strip()
            if current_module is not None:
                modules.append(current_module)
            current_module = Module(name)
        else:
            if current_module is not None:
                current_module.code.append(line)
    if current_module is not None:
        modules.append(current_module)
    return modules


def generate_agents(
    agent_code_lines: List[str],
    modules: List[Module],
    agent_data: List[Dict[str, Any]],
    agent_updates: AioQueue,
) -> List[Agent]:
    agent_logger = logging.getLogger("agent")
    agent_logger.setLevel(level=os.environ.get("LOG_LEVEL_AGENT", "INFO"))

    code_without_imports = remove_imports(agent_code_lines)

    # God please forgive me for what I'm about to do
    for module in modules:
        for imp in module.imports:
            exec(imp)
        # I do not exactly know why this works with proper scoping, so don't change it
        exec(f"{module.name} = module.import_code()", globals(), locals()) 

    exec("\n".join(code_without_imports))

    agents = []
    for agent_data_dict in agent_data:
        agent_type = agent_data_dict["type"]
        del agent_data_dict["type"]
        agent = locals()[agent_type](
            password=communication_server_settings.password,
            backup_method="queue",
            backup_queue=agent_updates,
            backup_period=backup_settings.period,
            backup_delay=backup_settings.delay,
            logger=agent_logger,
            **agent_data_dict,
        )
        agents.append(agent)

    logger.debug(f"Initialized agents: {agents}")

    return agents

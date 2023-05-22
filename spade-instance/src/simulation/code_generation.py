from __future__ import annotations

import copy
import datetime
import logging
import os
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


def generate_agents(
    agent_code_lines: List[str],
    agent_data: List[Dict[str, Any]],
    agent_updates: AioQueue,
) -> List[Agent]:
    agent_logger = logging.getLogger("agent")
    agent_logger.setLevel(level=os.environ.get("LOG_LEVEL_AGENT", "INFO"))

    code_without_imports = remove_imports(agent_code_lines)

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

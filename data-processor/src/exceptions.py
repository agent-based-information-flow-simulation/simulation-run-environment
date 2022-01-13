from __future__ import annotations


class SimulationBackupAlreadyExistsException(Exception):
    def __init__(self, simulation_id: str):
        super().__init__(f"[simulation {simulation_id}] Backup already exists")


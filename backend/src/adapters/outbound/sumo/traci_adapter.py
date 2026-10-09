import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

from domain.entities import SimulationScenario


class SumoNotAvailableError(RuntimeError):
    """Explains how to enable SUMO instead of failing with an opaque import error."""


class SumoTrafficSimulator:
    def __init__(self, sumo_binary: str = "sumo") -> None:
        self._binary = sumo_binary
        self._configuration: Path | None = None
        self._traci: ModuleType | None = None

    def _client(self) -> ModuleType:
        if self._traci is None:
            try:
                self._traci = importlib.import_module("traci")
            except ImportError as exc:
                raise SumoNotAvailableError(
                    "SUMO/TraCI is not installed. Install SUMO and expose its tools directory "
                    "through PYTHONPATH before running simulations."
                ) from exc
        return self._traci

    def load_scenario(self, scenario: SimulationScenario) -> None:
        configured = scenario.configuration.get("sumo_config")
        if not configured:
            raise ValueError("Scenario requires a validated 'sumo_config' path")
        path = Path(str(configured))
        if not path.is_file():
            raise FileNotFoundError(f"SUMO configuration not found: {path}")
        self._configuration = path

    def start_simulation(self) -> None:
        if self._configuration is None:
            raise RuntimeError("Load a validated scenario before starting SUMO")
        self._client().start([self._binary, "-c", str(self._configuration)])

    def stop_simulation(self) -> None:
        if self._traci is not None:
            self._traci.close()

    def set_traffic_demand(self, demand: dict[str, Any]) -> None:
        # TODO: map validated corridor demand inputs to SUMO routes/flows.
        _ = demand

    def get_vehicle_count(self) -> int:
        return int(self._client().vehicle.getIDCount())

    def get_average_speed(self) -> float:
        ids = self._client().vehicle.getIDList()
        return (
            sum(self._client().vehicle.getSpeed(vehicle_id) for vehicle_id in ids)
            / len(ids)
            if ids
            else 0.0
        )

    def get_queue_length(self) -> float:
        return float(
            sum(
                self._client().lane.getLastStepHaltingNumber(lane_id)
                for lane_id in self._client().lane.getIDList()
            )
        )

    def run_steps(self, steps: int) -> None:
        for _ in range(steps):
            self._client().simulationStep()

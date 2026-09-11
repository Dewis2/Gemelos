from typing import Any

from domain.entities import SimulationScenario


class FakeTrafficSimulator:
    """Deterministic simulator test double; its values are not empirical findings."""

    def __init__(self, average_speed: float = 0.0, queue_length: float = 0.0) -> None:
        self.average_speed = average_speed
        self.queue_length = queue_length
        self.started = False
        self.scenario: SimulationScenario | None = None

    def start_simulation(self) -> None:
        self.started = True

    def stop_simulation(self) -> None:
        self.started = False

    def load_scenario(self, scenario: SimulationScenario) -> None:
        self.scenario = scenario

    def set_traffic_demand(self, demand: dict[str, Any]) -> None:
        _ = demand

    def get_vehicle_count(self) -> int:
        return 0

    def get_average_speed(self) -> float:
        return self.average_speed

    def get_queue_length(self) -> float:
        return self.queue_length

    def run_steps(self, steps: int) -> None:
        if not self.started:
            raise RuntimeError("Simulation has not been started")
        if steps < 1:
            raise ValueError("steps must be positive")

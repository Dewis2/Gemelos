from uuid import UUID

from application.ports.outbound import (
    RoadNetworkRepository,
    ScenarioRepository,
    SimulationRepository,
    TrafficSimulatorPort,
)
from domain.entities import SimulationResult, SimulationScenario
from domain.exceptions import EntityNotFoundError


class CreateSimulationScenario:
    def __init__(self, repository: ScenarioRepository) -> None:
        self._repository = repository

    def execute(self, scenario: SimulationScenario) -> SimulationScenario:
        return self._repository.add(scenario)


class RunSimulationScenario:
    def __init__(
        self,
        scenarios: ScenarioRepository,
        results: SimulationRepository,
        network: RoadNetworkRepository,
        simulator: TrafficSimulatorPort,
    ) -> None:
        self._scenarios = scenarios
        self._results = results
        self._network = network
        self._simulator = simulator

    def execute(self, scenario_id: UUID) -> list[SimulationResult]:
        scenario = self._scenarios.get(scenario_id)
        if scenario is None:
            raise EntityNotFoundError(f"Scenario {scenario_id} was not found")
        self._simulator.load_scenario(scenario)
        self._simulator.start_simulation()
        try:
            self._simulator.set_traffic_demand(scenario.configuration.get("demand", {}))
            self._simulator.run_steps(int(scenario.configuration.get("steps", 1)))
            generated = [
                SimulationResult(
                    scenario_id=scenario.id,
                    road_segment_id=segment.id,
                    travel_time=0.0,
                    average_speed=self._simulator.get_average_speed(),
                    delay=0.0,
                    queue_length=self._simulator.get_queue_length(),
                    emissions={},
                )
                for segment in self._network.list_segments()
            ]
            # Zero placeholders are adapter observations only; real SUMO mapping is pending.
            return self._results.add_all(generated)
        finally:
            self._simulator.stop_simulation()


class CompareSimulationScenarios:
    def __init__(self, results: SimulationRepository) -> None:
        self._results = results

    def execute(self, scenario_ids: list[UUID]) -> dict[str, dict[str, float | int]]:
        comparison: dict[str, dict[str, float | int]] = {}
        for scenario_id in scenario_ids:
            values = self._results.by_scenario(scenario_id)
            count = len(values)
            comparison[str(scenario_id)] = {
                "result_count": count,
                "average_speed": (
                    sum(item.average_speed for item in values) / count if count else 0.0
                ),
                "average_delay": (
                    sum(item.delay for item in values) / count if count else 0.0
                ),
                "average_queue_length": (
                    sum(item.queue_length for item in values) / count if count else 0.0
                ),
            }
        return comparison


class GetSimulationResults:
    def __init__(self, results: SimulationRepository) -> None:
        self._results = results

    def execute(self, scenario_id: UUID) -> list[SimulationResult]:
        return self._results.by_scenario(scenario_id)

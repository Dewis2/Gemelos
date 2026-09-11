from __future__ import annotations

from typing import overload
from uuid import UUID

from domain.entities import (
    Intersection,
    RoadSegment,
    SimulationResult,
    SimulationScenario,
    TrafficMeasurement,
    TrafficPrediction,
)


class InMemoryStore:
    """Small development adapter; data is discarded when the process stops."""

    def __init__(self) -> None:
        self.measurements: list[TrafficMeasurement] = []
        self.intersections: list[Intersection] = []
        self.segments: list[RoadSegment] = []
        self.predictions: list[TrafficPrediction] = []
        self.scenarios: dict[UUID, SimulationScenario] = {}
        self.results: list[SimulationResult] = []

    @overload
    def add(self, item: TrafficMeasurement) -> TrafficMeasurement: ...

    @overload
    def add(self, item: TrafficPrediction) -> TrafficPrediction: ...

    @overload
    def add(self, item: SimulationScenario) -> SimulationScenario: ...

    def add(
        self, item: TrafficMeasurement | TrafficPrediction | SimulationScenario
    ) -> TrafficMeasurement | TrafficPrediction | SimulationScenario:
        if isinstance(item, TrafficMeasurement):
            self.measurements.append(item)
        elif isinstance(item, TrafficPrediction):
            self.predictions.append(item)
        elif isinstance(item, SimulationScenario):
            self.scenarios[item.id] = item
        else:
            raise TypeError(f"Unsupported entity: {type(item).__name__}")
        return item

    def latest(self) -> list[TrafficMeasurement]:
        return sorted(self.measurements, key=lambda item: item.timestamp, reverse=True)[:100]

    def list_segments(self) -> list[RoadSegment]:
        return list(self.segments)

    def list_intersections(self) -> list[Intersection]:
        return list(self.intersections)

    def get(self, scenario_id: UUID) -> SimulationScenario | None:
        return self.scenarios.get(scenario_id)

    def list_scenarios(self) -> list[SimulationScenario]:
        return list(self.scenarios.values())

    def add_all(self, results: list[SimulationResult]) -> list[SimulationResult]:
        self.results.extend(results)
        return results

    def by_scenario(self, scenario_id: UUID) -> list[SimulationResult]:
        return [item for item in self.results if item.scenario_id == scenario_id]

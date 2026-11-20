from typing import Any

from application.ports.outbound import ExploratorySimulationPort


class GetExploratoryReport:
    def __init__(self, simulation: ExploratorySimulationPort) -> None:
        self._simulation = simulation

    def execute(self) -> dict[str, Any]:
        return self._simulation.report()


class RunExploratorySimulation:
    def __init__(self, simulation: ExploratorySimulationPort) -> None:
        self._simulation = simulation

    def execute(self, level: str) -> dict[str, Any]:
        return self._simulation.run(level)

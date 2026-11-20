from typing import Any

from application.use_cases.exploratory_simulation import (
    GetExploratoryReport,
    RunExploratorySimulation,
)


class FakeExploratorySimulation:
    def __init__(self) -> None:
        self.levels: list[str] = []

    def report(self) -> dict[str, Any]:
        return {"study_type": "exploratory_uncalibrated"}

    def run(self, level: str) -> dict[str, Any]:
        self.levels.append(level)
        return {"level": level, "vehicles_arrived": 225}


def test_exploratory_use_cases_depend_only_on_the_output_port() -> None:
    simulation = FakeExploratorySimulation()

    assert GetExploratoryReport(simulation).execute()["study_type"] == ("exploratory_uncalibrated")
    assert RunExploratorySimulation(simulation).execute("normal") == {
        "level": "normal",
        "vehicles_arrived": 225,
    }
    assert simulation.levels == ["normal"]

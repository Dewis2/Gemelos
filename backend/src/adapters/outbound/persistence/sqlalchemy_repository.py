from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import (
    Intersection,
    RoadSegment,
    SimulationResult,
    SimulationScenario,
    TrafficMeasurement,
    TrafficPrediction,
)
from infrastructure.database.models import (
    IntersectionModel,
    RoadSegmentModel,
    SimulationResultModel,
    SimulationScenarioModel,
    TrafficMeasurementModel,
    TrafficPredictionModel,
)


class SqlAlchemyTrafficRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, measurement: TrafficMeasurement) -> TrafficMeasurement:
        row = TrafficMeasurementModel.from_domain(measurement)
        self._session.add(row)
        self._session.commit()
        return measurement

    def latest(self) -> list[TrafficMeasurement]:
        statement = (
            select(TrafficMeasurementModel)
            .order_by(TrafficMeasurementModel.timestamp.desc())
            .limit(100)
        )
        return [row.to_domain() for row in self._session.scalars(statement)]


class SqlAlchemyPredictionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, prediction: TrafficPrediction) -> TrafficPrediction:
        self._session.add(TrafficPredictionModel.from_domain(prediction))
        self._session.commit()
        return prediction


class SqlAlchemyScenarioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, scenario: SimulationScenario) -> SimulationScenario:
        self._session.add(SimulationScenarioModel.from_domain(scenario))
        self._session.commit()
        return scenario

    def get(self, scenario_id: UUID) -> SimulationScenario | None:
        row = self._session.get(SimulationScenarioModel, scenario_id)
        return row.to_domain() if row else None

    def list_scenarios(self) -> list[SimulationScenario]:
        return [row.to_domain() for row in self._session.scalars(select(SimulationScenarioModel))]


class SqlAlchemyRoadNetworkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_segments(self) -> list[RoadSegment]:
        return [
            row.to_domain()
            for row in self._session.scalars(
                select(RoadSegmentModel).order_by(RoadSegmentModel.name)
            )
        ]

    def list_intersections(self) -> list[Intersection]:
        return [
            row.to_domain()
            for row in self._session.scalars(
                select(IntersectionModel).order_by(IntersectionModel.name)
            )
        ]


class SqlAlchemySimulationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, results: list[SimulationResult]) -> list[SimulationResult]:
        self._session.add_all([SimulationResultModel.from_domain(item) for item in results])
        self._session.commit()
        return results

    def by_scenario(self, scenario_id: UUID) -> list[SimulationResult]:
        statement = select(SimulationResultModel).where(
            SimulationResultModel.scenario_id == scenario_id
        )
        return [row.to_domain() for row in self._session.scalars(statement)]

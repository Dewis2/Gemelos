from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

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
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, measurement: TrafficMeasurement) -> TrafficMeasurement:
        row = TrafficMeasurementModel.from_domain(measurement)
        with self._session_factory.begin() as session:
            session.add(row)
        return measurement

    def latest(self) -> list[TrafficMeasurement]:
        statement = (
            select(TrafficMeasurementModel)
            .order_by(TrafficMeasurementModel.timestamp.desc())
            .limit(100)
        )
        with self._session_factory() as session:
            return [row.to_domain() for row in session.scalars(statement)]


class SqlAlchemyPredictionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, prediction: TrafficPrediction) -> TrafficPrediction:
        with self._session_factory.begin() as session:
            session.add(TrafficPredictionModel.from_domain(prediction))
        return prediction


class SqlAlchemyScenarioRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, scenario: SimulationScenario) -> SimulationScenario:
        with self._session_factory.begin() as session:
            session.add(SimulationScenarioModel.from_domain(scenario))
        return scenario

    def get(self, scenario_id: UUID) -> SimulationScenario | None:
        with self._session_factory() as session:
            row = session.get(SimulationScenarioModel, scenario_id)
            return row.to_domain() if row else None

    def list_scenarios(self) -> list[SimulationScenario]:
        with self._session_factory() as session:
            statement = select(SimulationScenarioModel).order_by(
                SimulationScenarioModel.created_at.desc()
            )
            return [row.to_domain() for row in session.scalars(statement)]


class SqlAlchemyRoadNetworkRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_segments(self) -> list[RoadSegment]:
        with self._session_factory() as session:
            return [
                row.to_domain()
                for row in session.scalars(select(RoadSegmentModel).order_by(RoadSegmentModel.name))
            ]

    def list_intersections(self) -> list[Intersection]:
        with self._session_factory() as session:
            return [
                row.to_domain()
                for row in session.scalars(
                    select(IntersectionModel).order_by(IntersectionModel.name)
                )
            ]


class SqlAlchemySimulationRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add_all(self, results: list[SimulationResult]) -> list[SimulationResult]:
        with self._session_factory.begin() as session:
            session.add_all([SimulationResultModel.from_domain(item) for item in results])
        return results

    def by_scenario(self, scenario_id: UUID) -> list[SimulationResult]:
        statement = select(SimulationResultModel).where(
            SimulationResultModel.scenario_id == scenario_id
        )
        with self._session_factory() as session:
            return [row.to_domain() for row in session.scalars(statement)]

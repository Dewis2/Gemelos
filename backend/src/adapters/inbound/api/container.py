import json
from pathlib import Path

import paho.mqtt.client as mqtt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from adapters.outbound.datasets import (
    HuancayoHistoricalAdapter,
    MtcTollFlowAdapter,
    MtcTollLocationAdapter,
    OsitranRoadTrafficAdapter,
)
from adapters.outbound.ml import JoblibTrafficModel
from adapters.outbound.mqtt import LoggingEventPublisher, MqttEventPublisher
from adapters.outbound.persistence import (
    InMemoryStore,
    SqlAlchemyPredictionRepository,
    SqlAlchemyRoadNetworkRepository,
    SqlAlchemyScenarioRepository,
    SqlAlchemySimulationRepository,
    SqlAlchemyTrafficRepository,
    build_traffic_aggregate_repository,
)
from adapters.outbound.sumo import FakeTrafficSimulator
from application.ports.outbound import (
    EventPublisherPort,
    PredictionRepository,
    RoadNetworkRepository,
    ScenarioRepository,
    SimulationRepository,
    TrafficRepository,
)
from application.services import HistoricalReplayService, PeruDemoQueryService
from application.use_cases import (
    CompareSimulationScenarios,
    CreateSimulationScenario,
    GetDigitalTwinState,
    GetRoadNetwork,
    GetSimulationResults,
    PredictTrafficFlow,
    RegisterTrafficMeasurement,
    RunSimulationScenario,
)
from infrastructure.config import Settings
from infrastructure.corridor_reference import build_corridor


class ApplicationContainer:
    """Explicit composition root; swap adapters here without changing use cases."""

    def __init__(self, settings: Settings) -> None:
        self.engine = None
        self.session_factory = None
        if "sqlalchemy" in {settings.core_repository, settings.demo_repository}:
            self.engine = create_engine(settings.database_url, pool_pre_ping=True)
            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        traffic: TrafficRepository
        network: RoadNetworkRepository
        prediction: PredictionRepository
        scenario: ScenarioRepository
        simulation: SimulationRepository
        if settings.core_repository == "sqlalchemy":
            assert self.session_factory is not None
            from infrastructure.database.seed import seed_reference_data

            seed_reference_data(self.session_factory)
            traffic = SqlAlchemyTrafficRepository(self.session_factory)
            network = SqlAlchemyRoadNetworkRepository(self.session_factory)
            prediction = SqlAlchemyPredictionRepository(self.session_factory)
            scenario = SqlAlchemyScenarioRepository(self.session_factory)
            simulation = SqlAlchemySimulationRepository(self.session_factory)
        else:
            self.store = InMemoryStore()
            nodes, segments = build_corridor()
            self.store.intersections.extend(nodes)
            self.store.segments.extend(segments)
            traffic = network = prediction = scenario = simulation = self.store
        self.scenario_repository = scenario

        publisher = LoggingEventPublisher()
        simulator = FakeTrafficSimulator()
        model = JoblibTrafficModel(settings.ml_model_path)

        self.register_measurement = RegisterTrafficMeasurement(traffic, publisher)
        self.get_network = GetRoadNetwork(network)
        self.get_twin_state = GetDigitalTwinState(traffic, network)
        self.predict_traffic = PredictTrafficFlow(model, prediction, network)
        self.create_scenario = CreateSimulationScenario(scenario)
        self.run_scenario = RunSimulationScenario(scenario, simulation, network, simulator)
        self.get_simulation_results = GetSimulationResults(simulation)
        self.compare_scenarios = CompareSimulationScenarios(simulation)

        data_root = Path(settings.data_root)
        mtc_flow = MtcTollFlowAdapter(
            data_root / "external" / "mtc" / "toll_flow" / "raw" / "mtc_toll_flow.csv"
        )
        mtc_locations = MtcTollLocationAdapter(
            data_root / "external" / "mtc" / "toll_locations" / "raw" / "mtc_toll_locations.geojson"
        )
        ositran = OsitranRoadTrafficAdapter(
            data_root / "external" / "ositran" / "road_traffic" / "raw" / "ositran_road_traffic.csv"
        )
        huancayo = HuancayoHistoricalAdapter(
            data_root / "reference" / "huancayo_historical_counts.csv"
        )
        self.demo_query = PeruDemoQueryService(
            {
                mtc_flow.get_metadata().dataset_id: mtc_flow,
                mtc_locations.get_metadata().dataset_id: mtc_locations,
                ositran.get_metadata().dataset_id: ositran,
                huancayo.get_metadata().dataset_id: huancayo,
            },
            mtc_locations,
        )

        demo_repository = build_traffic_aggregate_repository(
            settings.demo_repository, session_factory=self.session_factory
        )
        if settings.demo_repository == "sqlalchemy":
            self.demo_query.set_repository(demo_repository)

        self.mqtt_client: mqtt.Client | None = None
        mqtt_active = False
        demo_publisher: EventPublisherPort = publisher
        if settings.mqtt_enabled:
            try:
                self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                self.mqtt_client.connect(settings.mqtt_host, settings.mqtt_port, 60)
                self.mqtt_client.loop_start()
                demo_publisher = MqttEventPublisher(self.mqtt_client)
                mqtt_active = True
            except OSError:
                self.mqtt_client = None
        self.demo_replay = HistoricalReplayService(
            self.demo_query,
            demo_repository,
            demo_publisher,
            mqtt_enabled=mqtt_active,
        )
        metadata_path = Path(settings.demo_ml_metadata_path)
        self.demo_ml_metadata: dict[str, object] | None = None
        if metadata_path.exists():
            self.demo_ml_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    def close(self) -> None:
        self.demo_replay.stop()
        if self.mqtt_client is not None:
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
        if self.engine is not None:
            self.engine.dispose()

import json
from pathlib import Path

import paho.mqtt.client as mqtt

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
    InMemoryTrafficAggregateRepository,
    SqlAlchemyTrafficAggregateRepository,
)
from adapters.outbound.sumo import FakeTrafficSimulator
from application.ports.outbound import EventPublisherPort, TrafficAggregateRepositoryPort
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


class ApplicationContainer:
    """Explicit composition root; swap adapters here without changing use cases."""

    def __init__(self, settings: Settings) -> None:
        self.store = InMemoryStore()
        publisher = LoggingEventPublisher()
        simulator = FakeTrafficSimulator()
        model = JoblibTrafficModel(settings.ml_model_path)

        self.register_measurement = RegisterTrafficMeasurement(self.store, publisher)
        self.get_network = GetRoadNetwork(self.store)
        self.get_twin_state = GetDigitalTwinState(self.store, self.store)
        self.predict_traffic = PredictTrafficFlow(model, self.store)
        self.create_scenario = CreateSimulationScenario(self.store)
        self.run_scenario = RunSimulationScenario(self.store, self.store, self.store, simulator)
        self.get_simulation_results = GetSimulationResults(self.store)
        self.compare_scenarios = CompareSimulationScenarios(self.store)

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

        demo_repository: TrafficAggregateRepositoryPort = InMemoryTrafficAggregateRepository()
        if settings.demo_repository == "sqlalchemy":
            from infrastructure.database.session import SessionFactory

            demo_repository = SqlAlchemyTrafficAggregateRepository(SessionFactory)

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

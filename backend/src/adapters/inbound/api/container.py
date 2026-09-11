from adapters.outbound.ml import JoblibTrafficModel
from adapters.outbound.mqtt import LoggingEventPublisher
from adapters.outbound.persistence import InMemoryStore
from adapters.outbound.sumo import FakeTrafficSimulator
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

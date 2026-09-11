from typing import Any

from application.ports.outbound import RoadNetworkRepository, TrafficRepository
from domain.entities import TrafficMeasurement


class GetDigitalTwinState:
    def __init__(self, traffic: TrafficRepository, network: RoadNetworkRepository) -> None:
        self._traffic = traffic
        self._network = network

    def execute(self) -> dict[str, Any]:
        measurements = self._traffic.latest()
        return {
            "status": "prototype",
            "corridor": "Av. Ferrocarril: Av. Giráldez–Av. Huancavelica",
            "road_segment_count": len(self._network.list_segments()),
            "intersection_count": len(self._network.list_intersections()),
            "latest_measurements": measurements,
            "geometry_status": "pending_validation",
        }


class UpdateDigitalTwinState:
    def __init__(self, traffic: TrafficRepository) -> None:
        self._traffic = traffic

    def execute(self, measurement: TrafficMeasurement) -> TrafficMeasurement:
        return self._traffic.add(measurement)

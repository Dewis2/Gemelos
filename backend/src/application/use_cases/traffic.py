from application.ports.outbound import EventPublisherPort, TrafficRepository
from domain.entities import TrafficMeasurement


class RegisterTrafficMeasurement:
    def __init__(
        self, repository: TrafficRepository, publisher: EventPublisherPort
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    def execute(self, measurement: TrafficMeasurement) -> TrafficMeasurement:
        saved = self._repository.add(measurement)
        self._publisher.publish(
            "huancayo/ferrocarril/events",
            {
                "event": "traffic_measurement.registered",
                "measurement_id": str(saved.id),
            },
        )
        return saved

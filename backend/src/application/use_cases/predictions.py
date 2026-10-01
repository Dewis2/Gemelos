from datetime import UTC, datetime

from application.dto import PredictionRequest
from application.ports.outbound import (
    MachineLearningPort,
    PredictionRepository,
    RoadNetworkRepository,
)
from domain.entities import TrafficPrediction
from domain.exceptions import EntityNotFoundError
from domain.value_objects import TrafficFeatures


class PredictTrafficFlow:
    """Caso de uso de entrada: valida el contrato del modelo y persiste la prediccion.

    Flujo hexagonal: `PredictionCommand` (puerto de entrada) -> esta clase ->
    `MachineLearningPort` / `PredictionRepository` / `RoadNetworkRepository`
    (puertos de salida) -> adaptadores concretos inyectados por el composition root.
    """

    def __init__(
        self,
        model: MachineLearningPort,
        repository: PredictionRepository,
        network: RoadNetworkRepository,
    ) -> None:
        self._model = model
        self._repository = repository
        self._network = network

    def execute(self, request: PredictionRequest) -> TrafficPrediction:
        # Regla de negocio: el vector debe cumplir el contrato completo del modelo.
        features = TrafficFeatures.from_mapping(request.features)

        # Regla de negocio: no se predice sobre un tramo que el gemelo no conoce.
        known_segments = {segment.id for segment in self._network.list_segments()}
        if request.road_segment_id not in known_segments:
            raise EntityNotFoundError(
                f"El tramo {request.road_segment_id} no está registrado en la red del corredor."
            )

        predicted_volume, version = self._model.predict_traffic(features.as_mapping())
        prediction = TrafficPrediction(
            road_segment_id=request.road_segment_id,
            prediction_timestamp=datetime.now(UTC),
            target_timestamp=request.target_timestamp,
            predicted_volume=max(0.0, predicted_volume),
            model_version=version,
        )
        return self._repository.add(prediction)
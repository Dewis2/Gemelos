from datetime import UTC, datetime

from application.dto import PredictionRequest
from application.ports.outbound import MachineLearningPort, PredictionRepository
from domain.entities import TrafficPrediction


class PredictTrafficFlow:
    def __init__(self, model: MachineLearningPort, repository: PredictionRepository) -> None:
        self._model = model
        self._repository = repository

    def execute(self, request: PredictionRequest) -> TrafficPrediction:
        predicted_volume, version = self._model.predict_traffic(request.features)
        prediction = TrafficPrediction(
            road_segment_id=request.road_segment_id,
            prediction_timestamp=datetime.now(UTC),
            target_timestamp=request.target_timestamp,
            predicted_volume=max(0.0, predicted_volume),
            model_version=version,
        )
        return self._repository.add(prediction)

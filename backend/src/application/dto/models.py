from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PredictionRequest:
    road_segment_id: UUID
    target_timestamp: datetime
    features: dict[str, float]

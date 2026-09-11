from typing import Any

from application.ports.outbound import RoadNetworkRepository


class GetRoadNetwork:
    def __init__(self, repository: RoadNetworkRepository) -> None:
        self._repository = repository

    def execute(self) -> dict[str, list[Any]]:
        return {
            "intersections": self._repository.list_intersections(),
            "road_segments": self._repository.list_segments(),
        }

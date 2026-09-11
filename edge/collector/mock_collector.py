from collections.abc import Iterable
from typing import Any


class MockCollector:
    """Yields explicitly supplied development records; it invents no observations."""

    def __init__(self, records: Iterable[dict[str, Any]]) -> None:
        self._records = iter(records)

    def receive(self) -> dict[str, Any]:
        return next(self._records)

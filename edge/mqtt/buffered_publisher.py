import json
from pathlib import Path
from typing import Any, Protocol


class Publisher(Protocol):
    def publish(self, topic: str, payload: str) -> Any: ...


class BufferedPublisher:
    def __init__(self, publisher: Publisher, buffer_path: Path) -> None:
        self._publisher = publisher
        self._buffer_path = buffer_path

    def publish(self, topic: str, payload: dict[str, Any]) -> bool:
        serialized = json.dumps(payload)
        try:
            self._publisher.publish(topic, serialized)
            return True
        except (OSError, RuntimeError, ConnectionError, TimeoutError):
            self._buffer_path.parent.mkdir(parents=True, exist_ok=True)
            with self._buffer_path.open("a", encoding="utf-8") as buffer:
                buffer.write(json.dumps({"topic": topic, "payload": payload}) + "\n")
            return False

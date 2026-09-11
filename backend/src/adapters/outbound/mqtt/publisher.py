import json
import logging
from typing import Any

import paho.mqtt.client as mqtt


class LoggingEventPublisher:
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        logging.getLogger(__name__).info("Event %s: %s", topic, payload)


class MqttEventPublisher:
    def __init__(self, client: mqtt.Client) -> None:
        self._client = client

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        info = self._client.publish(topic, json.dumps(payload, default=str), qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {info.rc}")

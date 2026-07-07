import json
import logging

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger(__name__)


class MQTTPublisher:
    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID_PUBLISHER)
        self._connected = False
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def connect(self):
        logger.info(f"[Publisher] Connecting to MQTT broker {settings.MQTT_BROKER}:{settings.MQTT_PORT} ...")
        self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=settings.MQTT_KEEPALIVE)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("[Publisher] MQTT Connected successfully.")
        else:
            self._connected = False
            logger.error(f"[Publisher] MQTT Connect failed with return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("[Publisher] Unexpected MQTT disconnect.")

    def publish_result(self, heart_rate: float, status: str, confidence: float = None) -> None:
        """
        Publishes the assessed result. confidence is optional (0-100 scale),
        carried over from the CV Layer's signal quality assessment.
        """
        payload = {
            "heartRate": heart_rate,
            "status": status,
        }

        if confidence is not None:
            payload["confidence"] = round(confidence)

        try:
            self.client.publish(settings.MQTT_TOPIC_PUBLISH, json.dumps(payload))
            logger.debug(f"[Publisher] Published to {settings.MQTT_TOPIC_PUBLISH}: {payload}")
        except Exception as e:
            logger.error(f"[Publisher] Failed to publish result: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    import time
    logging.basicConfig(level="DEBUG", format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    publisher = MQTTPublisher()
    publisher.connect()
    time.sleep(1)
    publisher.publish_result(heart_rate=82, status="NORMAL", confidence=98)
    time.sleep(1)
    publisher.publish_result(heart_rate=118, status="HIGH_RISK", confidence=91)
    time.sleep(1)
    publisher.stop()
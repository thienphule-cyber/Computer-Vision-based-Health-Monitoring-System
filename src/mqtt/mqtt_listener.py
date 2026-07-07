import json
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
from config import settings
logger = logging.getLogger(__name__)

class MQTTListener:
    def __init__(self, on_data_callback=None):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID_SUBSCRIBER)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.on_data_callback = on_data_callback
        self._connected = False

    def connect(self):
        logger.info(f"Connecting to MQTT broker {settings.MQTT_BROKER}:{settings.MQTT_PORT} ...")
        try:
            self.client.connect(
                settings.MQTT_BROKER,
                settings.MQTT_PORT,
                keepalive=settings.MQTT_KEEPALIVE
            )
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            raise

    def start(self):
        self.connect()
        self.client.loop_forever(retry_first_connection=True)

    def start_background(self):
        self.connect()
        self.client.loop_start()

    def stop(self):
        logger.info("Stopping MQTT listener...")
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("MQTT Connected successfully.")
            client.subscribe(settings.MQTT_TOPIC_SUBSCRIBE)
            logger.info(f"Subscribed to topic: {settings.MQTT_TOPIC_SUBSCRIBE}")
        else:
            self._connected = False
            logger.error(f"MQTT Connect failed with return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect (rc={rc}). Attempting reconnect...")
            self._reconnect_with_retry()
        else:
            logger.info("MQTT disconnected cleanly.")

    def _reconnect_with_retry(self):
        while not self._connected:
            try:
                time.sleep(settings.MQTT_RECONNECT_DELAY)
                logger.info("Reconnecting to MQTT broker...")
                self.client.reconnect()
                self._connected = True
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")

    def _on_message(self, client, userdata, msg):
        raw_payload = msg.payload.decode("utf-8", errors="replace")

        record = self._parse_json(raw_payload)
        if record is None:
            return
        
        record["received_at"] = datetime.now().isoformat(timespec="seconds")

        logger.info(f"Received data: {record}")

        if self.on_data_callback:
            try:
                self.on_data_callback(record)
            except Exception as e:
                logger.error(f"Error while processing record via callback: {e}")
        else:
            logger.warning("No on_data_callback registered. Record received but not processed further.")

    def _parse_json(self, raw_payload):
        try:
            return json.loads(raw_payload)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON received, discarding message. Error: {e}. Payload: {raw_payload}")
            return None
            
    def _log_raw_message(self, raw_payload):
        try:
            with open(settings.RAW_DATA_LOG_PATH, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat(timespec="seconds")
                f.write(f"{timestamp}\t{raw_payload}\n")
        except Exception as e:
            logger.error(f"Failed to write raw data log: {e}")

    @property
    def is_connected(self):
        return self._connected

if __name__ == "__main__":
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    def print_record(record):
        print(f"[TEST] New valid record received: {record}")

    listener = MQTTListener(on_data_callback=print_record)
    try:
        listener.start()

    except KeyboardInterrupt:
        listener.stop()


"""
MQTT subscriber for IoT soil sensor readings.

When MQTT_ENABLED=true, the API starts this subscriber on boot. Messages
are expected on topics like farm/soil/{field_id}/reading with JSON payload:

{
    "moisture_pct": 32.5,
    "ph": 6.4,
    "nitrogen_ppm": 40,
    "phosphorus_ppm": 25,
    "potassium_ppm": 150
}
"""

import json
import re
import threading
from typing import Optional

import config
from database.models import Field, SensorReading
from database.session import SessionLocal
from utils.logger import get_logger

logger = get_logger("mqtt_subscriber")

_client = None
_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

TOPIC_PATTERN = re.compile(r"farm/soil/(\d+)/reading")


def _on_message(client, userdata, msg):
    match = TOPIC_PATTERN.match(msg.topic)
    if not match:
        logger.warning(f"Ignoring message on unexpected topic: {msg.topic}")
        return

    field_id = int(match.group(1))
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error(f"Invalid MQTT payload on {msg.topic}: {exc}")
        return

    db = SessionLocal()
    try:
        field = db.query(Field).filter(Field.id == field_id).first()
        if not field:
            logger.warning(f"MQTT reading for unknown field_id={field_id}")
            return

        reading = SensorReading(
            field_id=field_id,
            moisture_pct=payload.get("moisture_pct"),
            ph=payload.get("ph"),
            nitrogen_ppm=payload.get("nitrogen_ppm"),
            phosphorus_ppm=payload.get("phosphorus_ppm"),
            potassium_ppm=payload.get("potassium_ppm"),
            source="mqtt",
        )
        db.add(reading)
        db.commit()
        logger.info(f"Stored MQTT soil reading for field {field_id}")
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to store MQTT reading: {exc}")
    finally:
        db.close()


def start_mqtt_subscriber() -> threading.Thread:
    global _client, _thread

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.error("paho-mqtt not installed. pip install paho-mqtt")
        return None

    _stop_event.clear()
    _client = mqtt.Client(client_id=config.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    _client.on_message = _on_message

    def _run():
        try:
            _client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            _client.subscribe(config.MQTT_TOPIC)
            logger.info(
                f"Subscribed to {config.MQTT_TOPIC} on "
                f"{config.MQTT_BROKER}:{config.MQTT_PORT}"
            )
            while not _stop_event.is_set():
                _client.loop(timeout=1.0)
        except Exception as exc:
            logger.error(f"MQTT subscriber error: {exc}")

    _thread = threading.Thread(target=_run, daemon=True, name="mqtt-subscriber")
    _thread.start()
    return _thread


def stop_mqtt_subscriber() -> None:
    global _client, _thread
    _stop_event.set()
    if _client is not None:
        _client.disconnect()
        _client = None
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None

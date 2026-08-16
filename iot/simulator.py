"""
Simple MQTT soil sensor simulator for demos and testing.

Example:
    python -m iot.simulator --field-id 1 --interval 10
"""

import argparse
import json
import random
import time

import config


def publish_reading(field_id: int, broker: str, port: int, interval: float):
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        raise SystemExit("Install paho-mqtt: pip install paho-mqtt")

    client = mqtt.Client(client_id=f"simulator-field-{field_id}")
    client.connect(broker, port, keepalive=60)
    topic = f"farm/soil/{field_id}/reading"

    print(f"Publishing simulated readings to {topic} every {interval}s")
    try:
        while True:
            payload = {
                "moisture_pct": round(random.uniform(15, 70), 1),
                "ph": round(random.uniform(5.5, 7.5), 1),
                "nitrogen_ppm": round(random.uniform(20, 60), 1),
                "phosphorus_ppm": round(random.uniform(15, 40), 1),
                "potassium_ppm": round(random.uniform(100, 200), 1),
            }
            client.publish(topic, json.dumps(payload))
            print(f"  -> {payload}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
    finally:
        client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="MQTT soil sensor simulator")
    parser.add_argument("--field-id", type=int, required=True)
    parser.add_argument("--broker", default=config.MQTT_BROKER)
    parser.add_argument("--port", type=int, default=config.MQTT_PORT)
    parser.add_argument("--interval", type=float, default=15.0)
    args = parser.parse_args()
    publish_reading(args.field_id, args.broker, args.port, args.interval)


if __name__ == "__main__":
    main()

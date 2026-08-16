"""
FastAPI application entry point for the Precision Agriculture Platform.

Run locally:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from api.routes import alerts, auth, fields, reports, sensors
from database.session import init_db
from utils.logger import get_logger

logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized.")

    mqtt_thread = None
    if config.MQTT_ENABLED:
        from iot.mqtt_subscriber import start_mqtt_subscriber

        mqtt_thread = start_mqtt_subscriber()
        logger.info("MQTT subscriber started.")

    yield

    if mqtt_thread is not None:
        from iot.mqtt_subscriber import stop_mqtt_subscriber

        stop_mqtt_subscriber()
        logger.info("MQTT subscriber stopped.")


app = FastAPI(
    title="Multi-Agent Precision Agriculture Platform",
    description="BIS685 - Crop advisory, disease prediction, and farm decisions",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(fields.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "precision-agriculture-platform"}

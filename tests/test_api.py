"""
API integration tests. Uses an in-memory SQLite database and mocks the
orchestrator so tests run offline without network/LLM/model calls.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app
from database.models import Base
from database.session import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


MOCK_PIPELINE_RESULT = {
    "crop_advisory": "Test advisory text.",
    "farm_decisions": [
        {
            "action": "irrigate",
            "priority": "high",
            "reason": "Soil moisture low.",
        }
    ],
    "weather_summary": {"rain_expected": False},
}


def register_and_login(client, email="farmer@test.com", password="secret12"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test Farmer"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login(client):
    headers = register_and_login(client)
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "farmer@test.com"


@patch("api.routes.reports.Orchestrator")
def test_run_report_creates_alerts(mock_orchestrator, client):
    mock_orchestrator.return_value.run.return_value = MOCK_PIPELINE_RESULT
    headers = register_and_login(client)

    response = client.post(
        "/api/reports/run",
        headers=headers,
        json={
            "crop": "wheat",
            "growth_stage": "flowering",
            "latitude": 12.97,
            "longitude": 77.59,
            "soil_data": {"moisture_pct": 15.0, "ph": 6.5},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["crop_advisory"] == "Test advisory text."
    assert body["farm_decisions"][0]["action"] == "irrigate"

    alerts = client.get("/api/alerts", headers=headers)
    assert alerts.status_code == 200
    assert len(alerts.json()) >= 1


def test_create_field_requires_auth(client):
    response = client.post(
        "/api/fields",
        json={
            "name": "North Plot",
            "crop": "wheat",
            "latitude": 12.97,
            "longitude": 77.59,
        },
    )
    assert response.status_code == 401

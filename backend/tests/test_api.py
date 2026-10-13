"""
API Integration Tests using FastAPI TestClient
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, seed_database_and_storage
from app.ml.schema import NUMERICAL_FEATURES

# Seed database before running tests
seed_database_and_storage()
client = TestClient(app)


def test_health_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"


def test_admin_and_client_login():
    # Admin login
    res_admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_admin.status_code == 200
    assert "access_token" in res_admin.json()
    assert res_admin.json()["role"] == "admin"

    # Client 0 login
    res_c0 = client.post("/auth/login", json={"username": "client_0", "password": "clientpass123"})
    assert res_c0.status_code == 200
    assert res_c0.json()["role"] == "client"
    assert res_c0.json()["client_id"] == 0


def test_role_based_access_control():
    # Client token trying to access Admin-only /clients endpoint
    c0_token = client.post("/auth/login", json={"username": "client_0", "password": "clientpass123"}).json()["access_token"]
    res_forbidden = client.get("/clients", headers={"Authorization": f"Bearer {c0_token}"})
    assert res_forbidden.status_code == 403

    # Admin accessing /clients
    admin_token = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    res_admin = client.get("/clients", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert len(res_admin.json()) == 4


def test_current_model_download():
    admin_token = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    res = client.get("/models/current", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "weights_base64" in res.json()


def test_predict_endpoint():
    admin_token = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    # Construct a valid synthetic record
    sample_record = {col: 0.0 for col in NUMERICAL_FEATURES}
    sample_record.update({
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF"
    })

    res = client.post("/predict", json={"records": [sample_record]}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["predictions"]) == 1
    assert "predicted_class_name" in data["predictions"][0]
    assert "probabilities" in data["predictions"][0]


def test_communication_metrics():
    admin_token = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    res = client.get("/metrics/communication", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["model_size_bytes"] > 0

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'marqueza-test.db'}",
        connect_args={"check_same_thread": False},
    )
    test_sessions = sessionmaker(bind=test_engine, expire_on_commit=False)
    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", test_sessions)
    monkeypatch.setattr(main.settings, "admin_password", "admin1234")
    with TestClient(main.app) as test_client:
        yield test_client
    test_engine.dispose()


def login(client, username="admin", password="admin1234"):
    response = client.post("/api/auth/login", json={"usuario": username, "contrasena": password})
    assert response.status_code == 200
    assert response.json()["token"] == response.json()["access_token"]
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_is_seeded_and_cannot_be_deleted(client):
    headers = login(client)
    users = client.get("/api/users", headers=headers)
    assert users.status_code == 200
    admin = users.json()[0]
    assert admin["nombre"] == "admin"
    assert admin["protegido"] is True

    changed = client.put(
        "/api/users/sync",
        headers=headers,
        json={"users": [{"id": admin["id"], "nombre": "otro", "correo": "otro@example.com", "rol": "Empleado", "activo": False}]},
    )
    assert changed.status_code == 200
    assert changed.json()[0]["nombre"] == "admin"
    assert changed.json()[0]["activo"] is True

    response = client.delete(f"/api/users/{admin['id']}", headers=headers)
    assert response.status_code == 403


def test_collection_persists_and_rejects_stale_version(client):
    headers = login(client)
    initial = client.get("/api/collections/clientes", headers=headers).json()
    assert initial == {"records": [], "version": 0}

    record = {"nombre": "Cliente Prueba", "documento": "123"}
    saved = client.put(
        "/api/collections/clientes",
        headers=headers,
        json={"records": [record], "version": initial["version"]},
    )
    assert saved.status_code == 200
    assert saved.json()["version"] == 1
    assert client.get("/api/collections/clientes", headers=headers).json()["records"] == [record]

    stale = client.put(
        "/api/collections/clientes",
        headers=headers,
        json={"records": [], "version": initial["version"]},
    )
    assert stale.status_code == 409


def test_registered_user_gets_employee_role(client):
    response = client.post(
        "/api/auth/register",
        json={"nombre": "empleado1", "correo": "empleado@example.com", "contrasena": "ClaveSegura123"},
    )
    assert response.status_code == 201
    assert response.json()["rol"] == "Empleado"
    assert response.json()["nombre"] == "empleado1"

    headers = login(client, "empleado1", "ClaveSegura123")
    assert client.get("/api/collections/clientes", headers=headers).status_code == 200
    assert client.get("/api/users", headers=headers).status_code == 403


def test_password_recovery_request_is_persisted_without_exposing_account(client):
    client.post(
        "/api/auth/register",
        json={"nombre": "empleado2", "correo": "empleado2@example.com", "contrasena": "ClaveSegura123"},
    )
    request = client.post("/api/auth/password-reset-requests", json={"correo": "empleado2@example.com"})
    assert request.status_code == 202
    assert "Si existe una cuenta" in request.json()["message"]

    headers = login(client)
    requests = client.get("/api/auth/password-reset-requests", headers=headers)
    assert requests.status_code == 200
    assert requests.json()[0]["correo"] == "empleado2@example.com"
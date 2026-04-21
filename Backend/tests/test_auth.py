from datetime import datetime, timezone

from bson import ObjectId
from fastapi.testclient import TestClient
import pytest

import main as backend_main
from app.routers import auth as auth_router
from main import app


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class FakeUserCollection:
    def __init__(self):
        self.documents: list[dict] = []

    async def find_one(self, query: dict):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    async def insert_one(self, document: dict):
        stored_document = dict(document)
        stored_document.setdefault("_id", ObjectId())
        stored_document.setdefault("created_at", datetime.now(timezone.utc))
        self.documents.append(stored_document)
        return FakeInsertResult(stored_document["_id"])


class FakeDatabase:
    def __init__(self):
        self.users = FakeUserCollection()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    fake_db = FakeDatabase()

    async def noop_async():
        return None

    monkeypatch.setattr(auth_router, "require_database", lambda: fake_db)
    monkeypatch.setattr(backend_main, "connect_to_mongodb", noop_async)
    monkeypatch.setattr(backend_main, "close_mongodb_connection", noop_async)
    monkeypatch.setattr(backend_main.xray_inference_service, "warmup", lambda: None)

    with TestClient(app) as test_client:
        yield test_client


def signup_user(client: TestClient, email: str = "test@example.com", password: str = "Secure123"):
    return client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
            "role": "patient",
        },
    )


def login_user(client: TestClient, email: str = "test@example.com", password: str = "Secure123"):
    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_signup(client: TestClient):
    response = signup_user(client)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "user_id" in data


def test_login(client: TestClient):
    signup_user(client)
    response = login_user(client)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient):
    signup_user(client)
    login_response = login_user(client)
    token = login_response.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_invalid_login(client: TestClient):
    signup_user(client)
    response = login_user(client, password="wrongpassword")
    assert response.status_code == 401


def test_duplicate_signup(client: TestClient):
    first_response = signup_user(client)
    second_response = signup_user(client)

    assert first_response.status_code == 201
    assert second_response.status_code == 400

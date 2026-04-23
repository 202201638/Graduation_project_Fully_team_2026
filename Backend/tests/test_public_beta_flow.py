from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi.testclient import TestClient
import pytest

import main as backend_main
from app.routers import auth as auth_router
from app.routers import patients as patients_router
from app.routers import xray_analysis as xray_router
from app.utils.xray_inference import SavedUpload
from main import app


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class FakeUpdateResult:
    modified_count = 1


class FakeDeleteResult:
    deleted_count = 1


class FakeCursor:
    def __init__(self, documents: list[dict]):
        self.documents = [dict(document) for document in documents]

    def sort(self, field_name: str, direction: int):
        reverse = direction < 0
        self.documents.sort(key=lambda item: item.get(field_name), reverse=reverse)
        return self

    async def to_list(self, length=None):
        return [dict(document) for document in self.documents]


class FakeCollection:
    def __init__(self):
        self.documents: list[dict] = []

    def _matches(self, document: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict) and "$in" in expected:
                if actual not in expected["$in"]:
                    return False
                continue

            if actual != expected:
                return False

        return True

    async def find_one(self, query: dict):
        for document in self.documents:
            if self._matches(document, query):
                return dict(document)
        return None

    async def insert_one(self, document: dict):
        stored_document = dict(document)
        stored_document.setdefault("_id", ObjectId())
        now = datetime.now(timezone.utc)
        stored_document.setdefault("created_at", now)
        stored_document.setdefault("updated_at", now)
        self.documents.append(stored_document)
        return FakeInsertResult(stored_document["_id"])

    def find(self, query: dict):
        return FakeCursor(
            [document for document in self.documents if self._matches(document, query)]
        )

    async def update_one(self, query: dict, update: dict):
        for index, document in enumerate(self.documents):
            if not self._matches(document, query):
                continue

            updated_document = dict(document)
            for key, value in update.get("$set", {}).items():
                updated_document[key] = value
            for key, value in update.get("$push", {}).items():
                updated_document.setdefault(key, []).append(value)
            self.documents[index] = updated_document
            return FakeUpdateResult()

        return FakeUpdateResult()

    async def delete_one(self, query: dict):
        for index, document in enumerate(self.documents):
            if self._matches(document, query):
                self.documents.pop(index)
                return FakeDeleteResult()
        return FakeDeleteResult()


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.patients = FakeCollection()
        self.xray_analyses = FakeCollection()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_db = FakeDatabase()

    async def noop_async():
        return None

    async def fake_save_upload(file):
        return SavedUpload(
            original_filename=file.filename or "scan.png",
            stored_filename="stored.png",
            file_path=tmp_path / "stored.png",
            image_url="/uploads/stored.png",
            file_size_bytes=128,
            image_width=64,
            image_height=64,
        )

    async def fake_run_inference(saved_upload, patient_id=None, scan_type=None, model_name=None):
        return {
            "analysis_id": "ANA_TEST_PUBLIC_BETA",
            "patient_id": patient_id,
            "scan_type": scan_type,
            "model_name": model_name or "fasterrcnn",
            "model_display_name": "Faster R-CNN",
            "model_family": "detection",
            "image_filename": saved_upload.original_filename,
            "result": {
                "pneumonia_detected": True,
                "suspected_pneumonia": False,
                "diagnosis_status": "pneumonia_detected",
                "confidence_score": 0.91,
                "findings": "Pneumonia region detected.",
                "recommendations": "Review with a clinician.",
                "analysis_details": {
                    "model_name": model_name or "fasterrcnn",
                    "model_display_name": "Faster R-CNN",
                    "model_family": "detection",
                },
                "detections": [
                    {
                        "label": "pneumonia",
                        "class_id": 0,
                        "confidence": 0.91,
                        "bbox": {"x1": 1, "y1": 2, "x2": 30, "y2": 40},
                    }
                ],
                "original_image_url": saved_upload.image_url,
                "rendered_image_url": "/uploads/rendered/stored_fasterrcnn_rendered.png",
            },
            "status": "completed",
            "processing_time": 0.01,
            "created_at": datetime.now(timezone.utc),
        }

    monkeypatch.setattr(auth_router, "require_database", lambda: fake_db)
    monkeypatch.setattr(patients_router, "require_database", lambda: fake_db)
    monkeypatch.setattr(xray_router, "require_database", lambda: fake_db)
    monkeypatch.setattr(xray_router, "_save_upload", fake_save_upload)
    monkeypatch.setattr(xray_router, "_run_inference", fake_run_inference)
    monkeypatch.setattr(backend_main, "connect_to_mongodb", noop_async)
    monkeypatch.setattr(backend_main, "close_mongodb_connection", noop_async)
    monkeypatch.setattr(backend_main.xray_inference_service, "warmup", lambda: None)

    with TestClient(app) as test_client:
        yield test_client


def signup_and_login(client: TestClient, email: str = "doctor@example.com"):
    password = "Secure123"
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "full_name": "Beta Doctor",
            "password": password,
            "role": "doctor",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def create_patient(client: TestClient, token: str, first_name: str):
    return client.post(
        "/api/patients/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "first_name": first_name,
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "phone": "01000000000",
            "address": "Cairo",
            "emergency_contact": "01000000001",
        },
    )


def test_new_doctor_can_manage_multiple_empty_patients(client: TestClient):
    token = signup_and_login(client)

    first = create_patient(client, token, "First")
    second = create_patient(client, token, "Second")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["medical_history"] == []
    assert first.json()["allergies"] == []
    assert first.json()["medications"] == []

    list_response = client.get(
        "/api/patients/list",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_cross_user_patient_access_is_rejected(client: TestClient):
    owner_token = signup_and_login(client, "owner@example.com")
    other_token = signup_and_login(client, "other@example.com")
    patient_response = create_patient(client, owner_token, "Private")
    patient_id = patient_response.json()["patient_id"]

    blocked_response = client.get(
        f"/api/patients/{patient_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert blocked_response.status_code == 404


def test_authenticated_upload_requires_owned_patient_and_persists_history(client: TestClient):
    token = signup_and_login(client)
    missing_patient_response = client.post(
        "/api/xray/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("scan.png", b"scan-bytes", "image/png")},
        data={"scan_type": "Chest X-ray"},
    )
    assert missing_patient_response.status_code == 400

    patient_response = create_patient(client, token, "Scan")
    patient_id = patient_response.json()["patient_id"]

    upload_response = client.post(
        "/api/xray/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("scan.png", b"scan-bytes", "image/png")},
        data={
            "patient_id": patient_id,
            "scan_type": "Chest X-ray",
            "model_name": "fasterrcnn",
        },
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["patient_id"] == patient_id
    assert upload_data["result"]["detections"][0]["label"] == "pneumonia"

    history_response = client.get(
        "/api/xray/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["analysis_id"] == "ANA_TEST_PUBLIC_BETA"
    assert history[0]["rendered_image_url"] == "/uploads/rendered/stored_fasterrcnn_rendered.png"


def test_authenticated_upload_rejects_cross_user_patient(client: TestClient):
    owner_token = signup_and_login(client, "scan-owner@example.com")
    other_token = signup_and_login(client, "scan-other@example.com")
    patient_response = create_patient(client, owner_token, "Private")
    patient_id = patient_response.json()["patient_id"]

    upload_response = client.post(
        "/api/xray/upload",
        headers={"Authorization": f"Bearer {other_token}"},
        files={"file": ("scan.png", b"scan-bytes", "image/png")},
        data={
            "patient_id": patient_id,
            "scan_type": "Chest X-ray",
            "model_name": "fasterrcnn",
        },
    )

    assert upload_response.status_code == 404

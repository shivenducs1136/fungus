"""API tests for demo booking endpoint."""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.core.database as db_module


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    db_path = tmp_path / "test_demo_booking.db"
    sql_alchemy_database_url = f"sqlite:///{db_path}"
    test_engine = create_engine(
        sql_alchemy_database_url, connect_args={"check_same_thread": False}
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", testing_session_local)

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_create_demo_booking_success(client, monkeypatch):
    import app.services.demo_booking_service as service_module

    monkeypatch.setattr(
        service_module.EmailService,
        "send_demo_booking_confirmation",
        lambda **kwargs: "sent",
    )

    payload = {
        "name": "Ada Lovelace",
        "work_email": "ada@company.com",
        "time": "10:30 AM UTC",
        "contact_number": "+14155552671",
        "short_note": "Need architecture walkthrough",
        "scheduled_datetime": "2026-08-20T10:30:00+00:00",
    }

    resp = client.post("/api/v1/demo-bookings/", json=payload)
    assert resp.status_code == 201

    body = resp.json()
    assert body["status"] == "created"
    assert body["name"] == payload["name"]
    assert body["work_email"] == payload["work_email"]
    assert body["time"] == payload["time"]
    assert body["contact_number"] == payload["contact_number"]
    assert body["short_note"] == payload["short_note"]
    assert body["email_status"] == "sent"
    assert "submitted_datetime" in body
    assert body["scheduled_datetime"] == payload["scheduled_datetime"]


def test_create_demo_booking_rejects_invalid_contact_number(client):
    payload = {
        "name": "Ada Lovelace",
        "work_email": "ada@company.com",
        "time": "10:30 AM UTC",
        "contact_number": "4155552671",
        "short_note": "Need architecture walkthrough",
        "scheduled_datetime": "2026-08-20T10:30:00+00:00",
    }

    resp = client.post("/api/v1/demo-bookings/", json=payload)
    assert resp.status_code == 422


def test_create_demo_booking_rejects_invalid_email(client):
    payload = {
        "name": "Ada Lovelace",
        "work_email": "ada-company.com",
        "time": "10:30 AM UTC",
        "contact_number": "+14155552671",
        "short_note": "Need architecture walkthrough",
        "scheduled_datetime": "2026-08-20T10:30:00+00:00",
    }

    resp = client.post("/api/v1/demo-bookings/", json=payload)
    assert resp.status_code == 422

"""Tests for API key auth, rate limiting, and CORS."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
import app.core.database as db_module


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine, "connect")
    def _pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", sessionmaker(autocommit=False, autoflush=False, bind=test_engine))
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ===========================================================================
# API KEY AUTH
# ===========================================================================

class TestApiKeyAuth:

    def test_request_with_valid_key_is_accepted(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "test-secret-key")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "false")
        # reload auth module so it picks up the new env var
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/api/v1/context/", headers={"X-API-Key": "test-secret-key"})
        assert resp.status_code == 200

    def test_request_without_key_returns_401(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "test-secret-key")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "false")
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/api/v1/context/")
        assert resp.status_code == 401

    def test_request_with_wrong_key_returns_401(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "test-secret-key")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "false")
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/api/v1/context/", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_auth_disabled_allows_requests_without_key(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "true")
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/api/v1/context/")
        assert resp.status_code == 200

    def test_missing_key_with_auth_enabled_returns_500(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "false")
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/context/")
        assert resp.status_code == 500

    def test_401_response_does_not_expose_server_internals(self, monkeypatch):
        monkeypatch.setenv("FUNGUS_API_KEY", "test-secret-key")
        monkeypatch.setenv("FUNGUS_AUTH_DISABLED", "false")
        import importlib
        import app.core.auth as auth_module
        importlib.reload(auth_module)
        import app.api.v1.context as ctx_module
        importlib.reload(ctx_module)

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.get("/api/v1/context/", headers={"X-API-Key": "wrong"})
        body = resp.text
        assert "traceback" not in body.lower()
        assert "postgresql" not in body.lower()
        assert "test-secret-key" not in body


# ===========================================================================
# CORS
# ===========================================================================

class TestCors:

    def test_allowed_origin_gets_cors_header(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.options(
                "/api/v1/context/",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_disallowed_origin_does_not_get_cors_header(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            resp = client.options(
                "/api/v1/context/",
                headers={
                    "Origin": "https://evil.attacker.com",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )
        assert resp.headers.get("access-control-allow-origin") != "https://evil.attacker.com"


# ===========================================================================
# DATABASE_URL GUARD
# ===========================================================================

class TestDatabaseUrlGuard:

    def test_missing_database_url_raises_at_import(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        import importlib
        import app.core.database as db
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            importlib.reload(db)

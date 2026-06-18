"""
Extensive API tests for the CRUD context endpoints.

Run with:  python -m pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """
    Redirect ContextService storage files to a fresh tmp directory for every
    test so tests are fully isolated and never touch the real JSON files.
    """
    from app.services import context_service as svc

    store_file = tmp_path / "knowledge_store.json"
    index_file = tmp_path / "jira_index.json"

    monkeypatch.setattr(svc.ContextService, "STORE_FILE", store_file)
    monkeypatch.setattr(svc.ContextService, "JIRA_INDEX_FILE", index_file)


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_entry(client, ticket_ids, content="some content", metadata=None):
    payload = {"ticket_ids": ticket_ids, "content": content}
    if metadata:
        payload["metadata"] = metadata
    resp = client.post("/api/v1/context/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ===========================================================================
# CREATE  POST /api/v1/context/
# ===========================================================================

class TestCreate:

    def test_create_single_ticket(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["PROJ-1"],
            "content": "Initial decision"
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["key"] == "[PROJ-1]"
        assert "entry_id" in body
        assert body["status"] == "created"

    def test_create_multiple_tickets_key_is_sorted(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["PROJ-3", "PROJ-1", "PROJ-2"],
            "content": "Multi-ticket entry"
        })
        assert resp.status_code == 201
        assert resp.json()["key"] == "[PROJ-1][PROJ-2][PROJ-3]"

    def test_create_duplicate_ticket_ids_deduped_in_key(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["PROJ-1", "PROJ-1"],
            "content": "Duplicate IDs"
        })
        assert resp.status_code == 201
        assert resp.json()["key"] == "[PROJ-1]"

    def test_create_expands_combined_bracketed_ticket_string(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["[ERP-24] [ERP-25]"],
            "content": "combined input"
        })
        assert resp.status_code == 201
        assert resp.json()["key"] == "[ERP-24][ERP-25]"

    def test_create_with_metadata(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["META-1"],
            "content": "With metadata",
            "metadata": {"author": "alice", "source": "test"}
        })
        assert resp.status_code == 201

    def test_create_multiple_entries_same_key(self, client):
        create_entry(client, ["SAME-1"], "first entry")
        create_entry(client, ["SAME-1"], "second entry")
        entries = client.get("/api/v1/context/[SAME-1]").json()
        assert len(entries) == 2

    def test_create_missing_content_returns_422(self, client):
        resp = client.post("/api/v1/context/", json={"ticket_ids": ["X-1"]})
        assert resp.status_code == 422

    def test_create_empty_ticket_ids_returns_422(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": [],
            "content": "no tickets"
        })
        assert resp.status_code == 422

    def test_create_blank_ticket_id_returns_422(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["   "],
            "content": "blank id"
        })
        assert resp.status_code == 422

    def test_create_invalid_bracketed_ticket_string_returns_422(self, client):
        resp = client.post("/api/v1/context/", json={
            "ticket_ids": ["[] []"],
            "content": "invalid bracket syntax"
        })
        assert resp.status_code == 422

    def test_create_returns_timestamp(self, client):
        body = create_entry(client, ["TS-1"], "entry")
        assert "timestamp" in body


# ===========================================================================
# LIST KEYS  GET /api/v1/context/
# ===========================================================================

class TestListKeys:

    def test_list_empty_store(self, client):
        resp = client.get("/api/v1/context/")
        assert resp.status_code == 200
        assert resp.json() == {"keys": []}

    def test_list_after_creates(self, client):
        create_entry(client, ["A-1"], "a")
        create_entry(client, ["B-1"], "b")
        create_entry(client, ["A-1", "B-1"], "ab")
        keys = client.get("/api/v1/context/").json()["keys"]
        assert set(keys) == {"[A-1]", "[B-1]", "[A-1][B-1]"}

    def test_list_does_not_duplicate_same_key(self, client):
        create_entry(client, ["DUP-1"], "first")
        create_entry(client, ["DUP-1"], "second")
        keys = client.get("/api/v1/context/").json()["keys"]
        assert keys.count("[DUP-1]") == 1


# ===========================================================================
# SEARCH BY JIRA ID  GET /api/v1/context/jira/{jira_id}
# ===========================================================================

class TestSearchByJira:

    def test_search_finds_single_ticket_entry(self, client):
        create_entry(client, ["SRCH-1"], "found me")
        results = client.get("/api/v1/context/jira/SRCH-1").json()
        assert len(results) == 1
        assert results[0]["content"] == "found me"

    def test_search_finds_entries_in_concatenated_key(self, client):
        create_entry(client, ["SRCH-1", "SRCH-2"], "multi-ticket entry")
        results = client.get("/api/v1/context/jira/SRCH-1").json()
        assert len(results) == 1
        assert results[0]["content"] == "multi-ticket entry"

    def test_search_finds_across_multiple_keys(self, client):
        create_entry(client, ["SRCH-1"], "solo entry")
        create_entry(client, ["SRCH-1", "SRCH-2"], "combined entry")
        results = client.get("/api/v1/context/jira/SRCH-1").json()
        assert len(results) == 2

    def test_search_jira_id_not_found_returns_404(self, client):
        resp = client.get("/api/v1/context/jira/NOPE-999")
        assert resp.status_code == 404

    def test_search_does_not_leak_unrelated_entries(self, client):
        create_entry(client, ["SRCH-1"], "relevant")
        create_entry(client, ["SRCH-2"], "irrelevant")
        results = client.get("/api/v1/context/jira/SRCH-1").json()
        contents = [e["content"] for e in results]
        assert "irrelevant" not in contents

    def test_search_is_case_sensitive(self, client):
        create_entry(client, ["srch-1"], "lowercase")
        resp = client.get("/api/v1/context/jira/SRCH-1")
        assert resp.status_code == 404


class TestRecentByJira:

    def test_recent_returns_most_recent_entries_by_depth(self, client):
        create_entry(client, ["REC-1"], "oldest")
        create_entry(client, ["REC-1"], "middle")
        create_entry(client, ["REC-1"], "newest")

        resp = client.get("/api/v1/context/jira/REC-1/recent", params={"depth": 2})
        assert resp.status_code == 200

        data = resp.json()
        assert len(data) == 2
        assert data[0]["content"] == "newest"
        assert data[1]["content"] == "middle"

    def test_recent_with_depth_larger_than_entries_returns_all(self, client):
        create_entry(client, ["REC-2"], "one")
        create_entry(client, ["REC-2"], "two")

        resp = client.get("/api/v1/context/jira/REC-2/recent", params={"depth": 10})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_recent_requires_positive_depth(self, client):
        create_entry(client, ["REC-3"], "entry")

        resp = client.get("/api/v1/context/jira/REC-3/recent", params={"depth": 0})
        assert resp.status_code == 422

    def test_recent_jira_not_found_returns_404(self, client):
        resp = client.get("/api/v1/context/jira/NOPE-1/recent", params={"depth": 2})
        assert resp.status_code == 404


# ===========================================================================
# READ ENTRIES BY KEY  GET /api/v1/context/{key}
# ===========================================================================

class TestGetByKey:

    def test_get_existing_key(self, client):
        create_entry(client, ["READ-1"], "hello")
        resp = client.get("/api/v1/context/[READ-1]")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert resp.json()[0]["content"] == "hello"

    def test_get_concatenated_key(self, client):
        create_entry(client, ["READ-1", "READ-2"], "combined")
        resp = client.get("/api/v1/context/[READ-1][READ-2]")
        assert resp.status_code == 200

    def test_get_nonexistent_key_returns_404(self, client):
        resp = client.get("/api/v1/context/GHOST-99")
        assert resp.status_code == 404

    def test_get_key_returns_all_entries(self, client):
        create_entry(client, ["READ-1"], "first")
        create_entry(client, ["READ-1"], "second")
        create_entry(client, ["READ-1"], "third")
        entries = client.get("/api/v1/context/[READ-1]").json()
        assert len(entries) == 3


# ===========================================================================
# READ SINGLE ENTRY  GET /api/v1/context/{key}/{entry_id}
# ===========================================================================

class TestGetEntry:

    def test_get_specific_entry(self, client):
        created = create_entry(client, ["ENT-1"], "specific content")
        key = created["key"]
        entry_id = created["entry_id"]
        resp = client.get(f"/api/v1/context/{key}/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["content"] == "specific content"

    def test_get_correct_entry_among_multiple(self, client):
        e1 = create_entry(client, ["ENT-1"], "entry one")
        e2 = create_entry(client, ["ENT-1"], "entry two")
        resp = client.get(f"/api/v1/context/[ENT-1]/{e2['entry_id']}")
        assert resp.json()["content"] == "entry two"

    def test_get_nonexistent_entry_id_returns_404(self, client):
        create_entry(client, ["ENT-1"], "exists")
        resp = client.get("/api/v1/context/[ENT-1]/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_get_entry_wrong_key_returns_404(self, client):
        created = create_entry(client, ["ENT-1"], "exists")
        resp = client.get(f"/api/v1/context/WRONG-KEY/{created['entry_id']}")
        assert resp.status_code == 404


# ===========================================================================
# UPDATE  PUT /api/v1/context/{key}/{entry_id}
# ===========================================================================

class TestUpdate:

    def test_update_content(self, client):
        created = create_entry(client, ["UPD-1"], "original")
        key, eid = created["key"], created["entry_id"]
        resp = client.put(f"/api/v1/context/{key}/{eid}", json={"content": "updated"})
        assert resp.status_code == 200
        assert resp.json()["content"] == "updated"

    def test_update_metadata(self, client):
        created = create_entry(client, ["UPD-1"], "content")
        key, eid = created["key"], created["entry_id"]
        resp = client.put(f"/api/v1/context/{key}/{eid}", json={
            "content": "content",
            "metadata": {"version": 2}
        })
        assert resp.json()["metadata"]["version"] == 2

    def test_update_persists(self, client):
        created = create_entry(client, ["UPD-1"], "old")
        key, eid = created["key"], created["entry_id"]
        client.put(f"/api/v1/context/{key}/{eid}", json={"content": "new"})
        fetched = client.get(f"/api/v1/context/{key}/{eid}").json()
        assert fetched["content"] == "new"

    def test_update_sets_updated_at(self, client):
        created = create_entry(client, ["UPD-1"], "content")
        key, eid = created["key"], created["entry_id"]
        resp = client.put(f"/api/v1/context/{key}/{eid}", json={"content": "new"})
        assert "updated_at" in resp.json()

    def test_update_does_not_affect_other_entries(self, client):
        e1 = create_entry(client, ["UPD-1"], "first")
        e2 = create_entry(client, ["UPD-1"], "second")
        client.put(f"/api/v1/context/[UPD-1]/{e1['entry_id']}", json={"content": "changed"})
        e2_fetched = client.get(f"/api/v1/context/[UPD-1]/{e2['entry_id']}").json()
        assert e2_fetched["content"] == "second"

    def test_update_nonexistent_entry_returns_404(self, client):
        resp = client.put("/api/v1/context/GHOST-1/bad-id", json={"content": "x"})
        assert resp.status_code == 404

    def test_update_missing_content_returns_422(self, client):
        created = create_entry(client, ["UPD-1"], "original")
        key, eid = created["key"], created["entry_id"]
        resp = client.put(f"/api/v1/context/{key}/{eid}", json={})
        assert resp.status_code == 422


# ===========================================================================
# DELETE  DELETE /api/v1/context/{key}/{entry_id}
# ===========================================================================

class TestDelete:

    def test_delete_entry(self, client):
        created = create_entry(client, ["DEL-1"], "to be deleted")
        key, eid = created["key"], created["entry_id"]
        resp = client.delete(f"/api/v1/context/{key}/{eid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_deleted_entry_no_longer_reachable(self, client):
        created = create_entry(client, ["DEL-1"], "gone")
        key, eid = created["key"], created["entry_id"]
        client.delete(f"/api/v1/context/{key}/{eid}")
        resp = client.get(f"/api/v1/context/{key}/{eid}")
        assert resp.status_code == 404

    def test_delete_last_entry_removes_key(self, client):
        created = create_entry(client, ["DEL-1"], "only entry")
        key, eid = created["key"], created["entry_id"]
        client.delete(f"/api/v1/context/{key}/{eid}")
        resp = client.get(f"/api/v1/context/{key}")
        assert resp.status_code == 404

    def test_delete_last_entry_removes_from_jira_index(self, client):
        created = create_entry(client, ["DEL-1"], "only entry")
        key, eid = created["key"], created["entry_id"]
        client.delete(f"/api/v1/context/{key}/{eid}")
        resp = client.get("/api/v1/context/jira/DEL-1")
        assert resp.status_code == 404

    def test_delete_one_entry_leaves_others(self, client):
        e1 = create_entry(client, ["DEL-1"], "keep me")
        e2 = create_entry(client, ["DEL-1"], "delete me")
        client.delete(f"/api/v1/context/[DEL-1]/{e2['entry_id']}")
        entries = client.get("/api/v1/context/[DEL-1]").json()
        assert len(entries) == 1
        assert entries[0]["content"] == "keep me"

    def test_delete_nonexistent_entry_returns_404(self, client):
        resp = client.delete("/api/v1/context/GHOST-1/bad-id")
        assert resp.status_code == 404

    def test_delete_jira_index_cleaned_when_key_removed(self, client):
        # Entry spans two JIRA IDs; after deletion both should be gone from index
        created = create_entry(client, ["DEL-1", "DEL-2"], "combined")
        key, eid = created["key"], created["entry_id"]
        client.delete(f"/api/v1/context/{key}/{eid}")
        assert client.get("/api/v1/context/jira/DEL-1").status_code == 404
        assert client.get("/api/v1/context/jira/DEL-2").status_code == 404


# ===========================================================================
# END-TO-END FLOW
# ===========================================================================

class TestEndToEnd:

    def test_full_crud_lifecycle(self, client):
        # CREATE
        created = create_entry(client, ["E2E-1", "E2E-2"], "initial", {"v": 1})
        key, eid = created["key"], created["entry_id"]
        assert key == "[E2E-1][E2E-2]"

        # READ via key
        entries = client.get(f"/api/v1/context/{key}").json()
        assert entries[0]["content"] == "initial"

        # READ via jira search
        results = client.get("/api/v1/context/jira/E2E-1").json()
        assert any(e["entry_id"] == eid for e in results)

        # UPDATE
        client.put(f"/api/v1/context/{key}/{eid}", json={"content": "revised", "metadata": {"v": 2}})
        updated = client.get(f"/api/v1/context/{key}/{eid}").json()
        assert updated["content"] == "revised"
        assert updated["metadata"]["v"] == 2

        # DELETE
        client.delete(f"/api/v1/context/{key}/{eid}")
        assert client.get(f"/api/v1/context/{key}").status_code == 404
        assert client.get("/api/v1/context/jira/E2E-1").status_code == 404

    def test_search_after_partial_delete(self, client):
        e1 = create_entry(client, ["MIX-1"], "standalone")
        e2 = create_entry(client, ["MIX-1", "MIX-2"], "combined")

        # Delete only the combined entry
        client.delete(f"/api/v1/context/[MIX-1][MIX-2]/{e2['entry_id']}")

        # MIX-1 still reachable via standalone entry
        results = client.get("/api/v1/context/jira/MIX-1").json()
        assert len(results) == 1
        assert results[0]["content"] == "standalone"

        # MIX-2 is now gone
        assert client.get("/api/v1/context/jira/MIX-2").status_code == 404

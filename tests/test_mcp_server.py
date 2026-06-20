"""Tests for the MCP stdio server tool handlers."""

import asyncio

import httpx

from app.mcp import server as mcp_server


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "http://test"),
                response=httpx.Response(self.status_code),
            )


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        return FakeResponse(
            201,
            {
                "status": "created",
                "key": "[ERP-24]",
                "entry_id": "entry-1",
                "timestamp": "2026-01-01T00:00:00Z",
            },
        )

    async def get(self, url, params=None):
        if "MISSING-1" in url:
            return FakeResponse(404, {"message": "not found"})
        return FakeResponse(
            200,
            [
                {
                    "entry_id": "entry-1",
                    "ticket_ids": ["[ERP-24]"],
                    "content": "Architectural reasoning",
                    "metadata": {},
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": None,
                }
            ],
        )


def test_save_architectural_knowledge_success(monkeypatch):
    monkeypatch.setattr(mcp_server.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        mcp_server.save_knowledge(
            jira_ids=["ERP-24"],
            chat_context="Decision rationale",
        )
    )

    assert "Context saved successfully" in result["message"]
    assert "[ERP-24]" in result["message"]


def test_retrieve_architectural_knowledge_handles_missing_jira(monkeypatch):
    monkeypatch.setattr(mcp_server.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        mcp_server.retrieve_knowledge(
            jira_ids=["ERP-24", "MISSING-1"],
            depth=2,
        )
    )

    assert "ERP-24" in result["message"]
    assert "Architectural reasoning" in result["message"]


def test_retrieve_knowledge_does_not_expose_db_shape(monkeypatch):
    monkeypatch.setattr(mcp_server.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        mcp_server.retrieve_knowledge(
            jira_ids=["ERP-24"],
            depth=3,
        )
    )

    assert "entry_id" not in result["message"]
    assert "created_at" not in result["message"]
    assert "updated_at" not in result["message"]
    assert "metadata" not in result["message"].lower()


def test_retrieve_architectural_knowledge_rejects_empty_input():
    result = asyncio.run(mcp_server.retrieve_knowledge(jira_ids=[]))
    assert "No jira_ids" in result["message"]


def test_retrieve_knowledge_from_code_uses_extracted_jira_ids(monkeypatch):
    monkeypatch.setattr(mcp_server.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        mcp_server,
        "_extract_jira_ids_for_code",
        lambda **kwargs: ["ERP-24", "MISSING-1"],
    )

    result = asyncio.run(
        mcp_server.retrieve_knowledge_from_code(
            file_path="app/main.py",
            start_line=10,
            end_line=20,
            depth=1,
        )
    )

    assert "ERP-24" in result["message"]
    assert "Architectural reasoning" in result["message"]


def test_save_knowledge_rejects_missing_chat_context():
    result = asyncio.run(mcp_server.save_knowledge(jira_ids=["ERP-24"]))
    assert "cannot read the active chat" in result["message"]


def test_format_retrieval_summary_merges_repetitive_points():
    repeated = (
        "Problem: Matrix dispatch is expensive.\n\n"
        "Decision: Use direct function pointers for known datatypes and matrix lookup for unknown datatypes.\n\n"
        "Alternatives considered: Keep optimizing keywords.\n\n"
        "Constraints: Unknown datatypes come from remote payloads.\n\n"
        "Impact/risk: Memory may increase.\n\n"
        "Validation performed: Reviewed existing expression engine behavior."
    )
    expanded = (
        "Problem: Matrix dispatch is expensive as datatype combinations grow.\n\n"
        "Decision: Use direct function pointers for known datatypes and matrix lookup for unknown datatypes with validation.\n\n"
        "Alternatives considered: Keep optimizing keywords.\n\n"
        "Constraints: Unknown datatypes come from remote payloads.\n\n"
        "Impact/risk: Memory may increase.\n\n"
        "Validation performed: Reviewed existing expression engine behavior thoroughly."
    )

    message = mcp_server._format_retrieval_summary(
        {
            "ERP-24": [
                {
                    "content": repeated,
                    "metadata": {"source": "copilot-chat"},
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": None,
                },
                {
                    "content": expanded,
                    "metadata": {"source": "copilot-chat"},
                    "created_at": "2026-01-02T00:00:00Z",
                    "updated_at": None,
                },
            ]
        }
    )

    assert message.count("**Decision:**") == 1
    assert message.count("- Use direct function pointers") == 1

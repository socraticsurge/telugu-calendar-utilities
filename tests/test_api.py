"""Contract and parity tests for the additive Vercel API adapter."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from telugu_panchangam.api.app import app
from telugu_panchangam.mcp.tools import tool_get_panchangam

TOKEN = "test-service-token-with-enough-entropy"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("PANCHANGAM_API_TOKEN", TOKEN)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def auth():
    return {"Authorization": f"Bearer {TOKEN}"}


def day_payload():
    return {
        "date": "2026-07-22",
        "city": "Hyderabad",
        "system": "drik",
        "ayanamsa": "lahiri",
    }


def test_health_is_public_and_minimal(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "PANCHANGAM_API_TOKEN" not in response.text
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize("header", [None, "Bearer wrong-token", "Basic value"])
def test_v1_requires_valid_bearer_token(client, header):
    headers = {} if header is None else {"Authorization": header}
    response = client.get("/v1/catalog", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_unconfigured_service_fails_closed(monkeypatch):
    monkeypatch.delenv("PANCHANGAM_API_TOKEN", raising=False)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/catalog", headers={"Authorization": "Bearer value"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_not_configured"


def test_weak_service_token_fails_closed(monkeypatch):
    monkeypatch.setenv("PANCHANGAM_API_TOKEN", "too-short")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/catalog", headers={"Authorization": "Bearer too-short"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_not_configured"


def test_catalog_is_bounded_and_has_no_cors(client):
    response = client.get("/v1/catalog", headers={**auth(), "Origin": "https://example.com"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["cities"]) == 22
    assert data["systems"] == ["drik", "surya_siddhanta", "vakya"]
    assert data["limits"]["muhurtam_days"] == 14
    assert "access-control-allow-origin" not in response.headers


def test_panchangam_day_matches_existing_tool(client):
    response = client.post("/v1/panchangam/day", headers=auth(), json=day_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    baseline = json.loads(tool_get_panchangam("2026-07-22", "Hyderabad", "drik"))
    for key, value in baseline.items():
        assert body["data"][key] == value
    assert len(body["data"]["horas"]) == 24
    assert len(body["data"]["choghadiya"]) == 8
    assert len(body["data"]["choghadiya_night"]) == 8
    assert body["data"]["choghadiya_night"][0]["start"] == body["data"]["sky"]["sunset"]
    assert body["data"]["choghadiya_night"][-1]["end"] == body["data"]["ghati_clock"]["next_sunrise"]
    assert body["data"]["lagna_transitions"]
    assert body["contract_version"] == "1.0"


def test_request_id_is_propagated_when_safe(client):
    response = client.post(
        "/v1/panchangam/day",
        headers={**auth(), "X-Request-ID": "web:gate5-123"},
        json=day_payload(),
    )
    assert response.headers["x-request-id"] == "web:gate5-123"
    assert response.json()["request_id"] == "web:gate5-123"


def test_invalid_request_id_is_replaced(client):
    response = client.get(
        "/health",
        headers={"X-Request-ID": "contains private data and spaces"},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "contains private data and spaces"


def test_validation_errors_are_redacted(client):
    payload = day_payload() | {"timezone": "not/a-real-zone", "private_note": "secret"}
    response = client.post("/v1/panchangam/day", headers=auth(), json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_request",
        "message": "Request validation failed.",
    }
    assert "secret" not in response.text
    assert "not/a-real-zone" not in response.text


def test_rejects_non_json_and_oversized_body(client):
    wrong_type = client.post("/v1/panchangam/day", headers=auth(), content="date=2026")
    assert wrong_type.status_code == 415
    too_large = client.post(
        "/v1/panchangam/day",
        headers={**auth(), "Content-Type": "application/json", "Content-Length": "65537"},
        content="{}",
    )
    assert too_large.status_code == 413
    actual_large_body = client.post(
        "/v1/panchangam/day",
        headers={**auth(), "Content-Type": "application/json"},
        content='{"padding":"' + ("x" * 66_000) + '"}',
    )
    assert actual_large_body.status_code == 413


def test_range_limit_is_inclusive_31_days(client):
    payload = {
        "start_date": "2026-06-01", "end_date": "2026-07-01",
        "city": "Hyderabad", "system": "drik", "ayanamsa": "lahiri",
    }
    allowed = client.post("/v1/panchangam/range", headers=auth(), json=payload)
    assert allowed.status_code == 200
    rejected = client.post(
        "/v1/panchangam/range", headers=auth(),
        json=payload | {"end_date": "2026-07-02"},
    )
    assert rejected.status_code == 422


def test_rasi_phalalu_exposes_computed_sky_positions(client):
    response = client.post(
        "/v1/rasi-phalalu",
        headers=auth(),
        json={
            "date": "2026-07-26",
            "city": "Hyderabad",
            "janma_rasi": "Mesha",
            "ayanamsa": "lahiri",
        },
    )
    assert response.status_code == 200, response.text
    positions = response.json()["data"]["sky_positions"]
    assert len(positions) == 9
    assert {position["graha"] for position in positions} >= {"Surya", "Chandra"}
    assert all(0 <= position["longitude"] < 360 for position in positions)


def test_public_muhurtam_is_useful_without_participants(client):
    response = client.post(
        "/v1/muhurtam/search",
        headers=auth(),
        json={
            "start_date": "2026-08-01", "days": 3, "activity": "travel",
            "city": "Hyderabad", "participants": [],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "slots" in body["data"]
    assert body["data"]["participants"] == []
    assert "tarabalam" in body["evidence"]["not_evaluated"]


def test_profile_muhurtam_names_only_request_local_labels(client):
    response = client.post(
        "/v1/muhurtam/search",
        headers=auth(),
        json={
            "start_date": "2026-08-01", "days": 1, "activity": "travel",
            "city": "Hyderabad",
            "participants": [{
                "label": "p1", "janma_nakshatra": "Ashvini",
                "janma_rasi": "Mesha", "janma_lagna": "Makara",
            }],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["participants"] == ["p1"]
    assert "tarabalam" in response.json()["evidence"]["evaluated_factors"]


def test_tarabalam_supports_90_days_by_joining_canonical_chunks(client):
    response = client.post(
        "/v1/tarabalam",
        headers=auth(),
        json={
            "start_date": "2026-01-01", "days": 90, "city": "Hyderabad",
            "participants": [{
                "label": "p1", "janma_nakshatra": "Ashvini", "janma_rasi": "Mesha",
            }],
        },
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["data"]["days"]) == 90


def test_tarabalam_rejects_non_lahiri_until_canonical_tool_supports_it(client):
    response = client.post(
        "/v1/tarabalam",
        headers=auth(),
        json={
            "start_date": "2026-01-01", "days": 1, "city": "Hyderabad",
            "ayanamsa": "raman",
            "participants": [{"label": "p1", "janma_nakshatra": "Ashvini"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_unexpected_errors_do_not_leak_exception_text(client, monkeypatch):
    def fail(_payload):
        raise RuntimeError("private birth details should never escape")

    monkeypatch.setattr("telugu_panchangam.api.service.panchangam_day", fail)
    response = client.post("/v1/panchangam/day", headers=auth(), json=day_payload())
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "calculation_failed"
    assert "private birth details" not in response.text


def test_unknown_routes_use_stable_error_shape(client):
    response = client.get("/v1/not-real", headers=auth())
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_vercel_manifest_uses_framework_level_fastapi_entrypoint():
    manifest = json.loads(Path("vercel.json").read_text())
    assert manifest["framework"] == "fastapi"
    assert manifest["regions"] == ["bom1"]
    assert manifest["functions"]["app.py"]["maxDuration"] == 60

    ignored = Path(".vercelignore").read_text().splitlines()
    assert "package.json" in ignored
    assert "tests/" in ignored

    from app import app as vercel_app

    assert vercel_app is app

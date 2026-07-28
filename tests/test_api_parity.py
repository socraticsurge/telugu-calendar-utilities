"""Cross-system/date/location parity for the additive HTTP adapter."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from telugu_panchangam.api.app import app
from telugu_panchangam.mcp.tools import (
    tool_find_muhurta,
    tool_find_tarabalam_days,
    tool_get_panchangam,
    tool_get_panchangam_range,
    tool_get_rasi_phalalu,
)

TOKEN = "parity-test-service-token-with-entropy"
FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "api_parity_cases.json").read_text()
)["cases"]


@pytest.fixture(scope="module")
def client():
    import os

    previous = os.environ.get("PANCHANGAM_API_TOKEN")
    os.environ["PANCHANGAM_API_TOKEN"] = TOKEN
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    if previous is None:
        os.environ.pop("PANCHANGAM_API_TOKEN", None)
    else:
        os.environ["PANCHANGAM_API_TOKEN"] = previous


def auth():
    return {"Authorization": f"Bearer {TOKEN}"}


def selected(data):
    return {
        "vaaram": data["metadata"]["vaaram"],
        "tithi": data["pancha_anga"]["tithi"]["name"],
        "nakshatra": data["pancha_anga"]["nakshatra"]["name"],
        "yoga": data["pancha_anga"]["yoga"]["name"],
        "sunrise": data["sky"]["sunrise"],
        "sunset": data["sky"]["sunset"],
        "rahu_kalam": data["inauspicious"]["rahu_kalam"],
        "special_days": data["special_days"],
    }


@pytest.mark.parametrize("case", FIXTURES, ids=[case["id"] for case in FIXTURES])
def test_day_endpoint_matches_frozen_fixture_and_existing_serializer(client, case):
    baseline = json.loads(tool_get_panchangam(
        case["date"], case["city"], case["system"], ayanamsa=case["ayanamsa"],
    ))
    assert selected(baseline) == case["expected"]

    response = client.post(
        "/v1/panchangam/day", headers=auth(),
        json={key: case[key] for key in ("date", "city", "system", "ayanamsa")},
    )
    assert response.status_code == 200, response.text
    api_data = response.json()["data"]
    assert selected(api_data) == case["expected"]
    for key, value in baseline.items():
        assert api_data[key] == value


def test_range_endpoint_matches_existing_serializer_at_dst_boundary(client):
    payload = {
        "start_date": "2026-03-28", "end_date": "2026-03-30",
        "city": "London", "system": "drik", "ayanamsa": "lahiri",
    }
    baseline = json.loads(tool_get_panchangam_range(
        payload["start_date"], payload["end_date"], payload["city"],
        payload["system"], ayanamsa=payload["ayanamsa"],
    ))
    response = client.post("/v1/panchangam/range", headers=auth(), json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["data"] == baseline


def test_rasi_phalalu_endpoint_matches_existing_serializer(client):
    payload = {
        "date": "2026-08-12", "city": "San Jose",
        "janma_rasi": "Mesha", "janma_nakshatra": "Ashvini",
        "ayanamsa": "lahiri",
    }
    baseline = json.loads(tool_get_rasi_phalalu(
        date_str=payload["date"], city=payload["city"],
        janma_rasi=payload["janma_rasi"], janma_nakshatra=payload["janma_nakshatra"],
        ayanamsa=payload["ayanamsa"],
    ))
    response = client.post("/v1/rasi-phalalu", headers=auth(), json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["data"] == baseline


def test_tarabalam_endpoint_matches_existing_serializer_for_canonical_span(client):
    payload = {
        "start_date": "2026-07-22", "days": 14, "city": "Hyderabad",
        "system": "drik", "ayanamsa": "lahiri", "chandra_mode": "puja_ok",
        "participants": [
            {"label": "p1", "janma_nakshatra": "Ashvini", "janma_rasi": "Mesha"},
            {"label": "p2", "janma_nakshatra": "Rohini", "janma_rasi": "Vrishabha"},
        ],
    }
    baseline = json.loads(tool_find_tarabalam_days(
        janma_nakshatras=["Ashvini", "Rohini"],
        janma_rasis=["Mesha", "Vrishabha"],
        start_date=payload["start_date"], days=payload["days"], city=payload["city"],
        system=payload["system"], chandra_mode=payload["chandra_mode"],
    ))
    response = client.post("/v1/tarabalam", headers=auth(), json=payload)
    assert response.status_code == 200, response.text
    api_data = response.json()["data"]
    for key, value in baseline.items():
        assert api_data[key] == value


@pytest.mark.parametrize("with_participant", [False, True])
def test_muhurtam_endpoint_matches_existing_serializer(client, with_participant):
    participants = ([{
        "label": "p1", "janma_nakshatra": "Ashvini",
        "janma_rasi": "Mesha", "janma_lagna": "Makara",
    }] if with_participant else [])
    payload = {
        "start_date": "2026-08-01", "days": 3, "activity": "travel",
        "city": "Hyderabad", "system": "drik", "ayanamsa": "lahiri",
        "chandra_mode": "stars", "participants": participants,
    }
    baseline = json.loads(tool_find_muhurta(
        start_date=payload["start_date"], days=payload["days"], activity=payload["activity"],
        city=payload["city"], system=payload["system"], ayanamsa=payload["ayanamsa"],
        chandra_mode=payload["chandra_mode"],
        janma_nakshatras=["Ashvini"] if with_participant else None,
        janma_rasis=["Mesha"] if with_participant else None,
        janma_lagnas=["Makara"] if with_participant else None,
    ))
    response = client.post("/v1/muhurtam/search", headers=auth(), json=payload)
    assert response.status_code == 200, response.text
    api_data = response.json()["data"]
    for key, value in baseline.items():
        assert api_data[key] == value

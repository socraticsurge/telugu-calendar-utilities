"""Independent formula-path reproduction for the guest birth-profile fixture.

The fixture is produced by DashaFlow, while this test derives the same narrow
contract directly from PySwissEph. Both paths share Swiss Ephemeris, so these
cells are explicitly reproduction checks rather than independent astronomy.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytz
import swisseph as swe

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "birth_profile_reference.json"

NAKSHATRAS = (
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
)
RASHIS = (
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
)
GRAHAS = (
    ("Surya", swe.SUN),
    ("Chandra", swe.MOON),
    ("Kuja", swe.MARS),
    ("Budha", swe.MERCURY),
    ("Guru", swe.JUPITER),
    ("Shukra", swe.VENUS),
    ("Shani", swe.SATURN),
    ("Rahu", swe.MEAN_NODE),
)


def _julian_day(case: dict) -> float:
    local = datetime.strptime(
        f"{case['date_of_birth']} {case['time_of_birth']}",
        "%Y-%m-%d %H:%M",
    )
    localized = pytz.timezone(case["timezone"]).localize(local, is_dst=None)
    utc = localized.astimezone(pytz.utc)
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour)


def _rashi(longitude: float) -> tuple[str, float, int]:
    normalized = longitude % 360
    index = int(normalized / 30)
    return RASHIS[index], round(normalized % 30, 2), index


def _ephemeris_name(flags: int) -> str:
    if flags & swe.FLG_MOSEPH:
        return "moshier"
    if flags & swe.FLG_SWIEPH:
        return "swiss"
    return "unknown"


def _derive(case: dict) -> dict:
    swe.set_ephe_path("")
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = _julian_day(case)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    _, ascmc = swe.houses_ex(
        jd,
        case["latitude"],
        case["longitude"],
        b"W",
        flags,
    )
    lagna, lagna_degree, lagna_index = _rashi(ascmc[0])

    planets: list[dict] = []
    raw_rahu_longitude = 0.0
    ephemeris = "unknown"
    moon_longitude = 0.0
    for name, planet_id in GRAHAS:
        values, return_flags = swe.calc_ut(jd, planet_id, flags)
        longitude = values[0]
        rashi, degree, rashi_index = _rashi(longitude)
        if name == "Surya":
            ephemeris = _ephemeris_name(return_flags)
        if name == "Chandra":
            moon_longitude = longitude
        if name == "Rahu":
            raw_rahu_longitude = longitude
        planets.append({
            "name": name,
            "rashi": rashi,
            "degree": degree,
            "house": ((rashi_index - lagna_index) % 12) + 1,
            "retrograde": name == "Rahu" or (
                name not in {"Surya", "Chandra"} and values[3] < 0
            ),
        })

    ketu_rashi, ketu_degree, ketu_index = _rashi(raw_rahu_longitude + 180)
    planets.append({
        "name": "Ketu",
        "rashi": ketu_rashi,
        "degree": ketu_degree,
        "house": ((ketu_index - lagna_index) % 12) + 1,
        "retrograde": True,
    })

    nakshatra_span = 360 / 27
    pada_span = 360 / 108
    moon = moon_longitude % 360
    nakshatra_index = int(moon / nakshatra_span)
    return {
        "nakshatra": NAKSHATRAS[nakshatra_index],
        "pada": int((moon - nakshatra_index * nakshatra_span) / pada_span) + 1,
        "janma_rashi": _rashi(moon)[0],
        "lagna": lagna,
        "lagna_degree": lagna_degree,
        "ephemeris": ephemeris,
        "planets": planets,
    }


def test_birth_profile_reference_cells_reproduce_the_contract() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text())
    assert fixture["assurance"] == "reproduction-checked"
    assert len(fixture["cases"]) == 3

    for case in fixture["cases"]:
        assert _derive(case["input"]) == case["expected"], case["id"]

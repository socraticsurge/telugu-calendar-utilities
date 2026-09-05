"""Tests for Nakshatra Mukha (mouth-direction) classification — Task 15."""
import json
from collections import Counter
from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.nakshatra_filters import NAKSHATRA_MUKHA, nakshatra_mukha


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


# ── Table correctness ───────────────────────────────────────────────────────

def test_table_covers_all_27_nakshatras():
    assert len(NAKSHATRA_MUKHA) == 27


def test_table_uses_three_classes_only():
    values = set(NAKSHATRA_MUKHA.values())
    assert values == {'Adho', 'Urdhva', 'Tiryan'}


def test_class_counts():
    # 10 Urdhva, 7 Adho, 10 Tiryan = 27
    counts = Counter(NAKSHATRA_MUKHA.values())
    assert counts['Urdhva'] == 10
    assert counts['Adho'] == 7
    assert counts['Tiryan'] == 10


def test_known_classifications():
    assert nakshatra_mukha('Mrigashira') == 'Urdhva'
    assert nakshatra_mukha('Krittika') == 'Adho'
    assert nakshatra_mukha('Ashvini') == 'Tiryan'


def test_unknown_returns_none():
    assert nakshatra_mukha('Foo') is None
    assert nakshatra_mukha(None) is None


# ── Engine wiring ───────────────────────────────────────────────────────────

def test_engine_populates_nakshatra_mukha():
    eng = DrikGanitaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.nakshatra_mukha in {'Adho', 'Urdhva', 'Tiryan'}


# ── MCP serialisation ───────────────────────────────────────────────────────

def test_mukha_in_all_mcp_tool_responses():
    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'nakshatra_mukha' in out1
    assert out1['nakshatra_mukha'] in {'Adho', 'Urdhva', 'Tiryan'}

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'nakshatra_mukha' in out2
    assert out2['nakshatra_mukha'] in {'Adho', 'Urdhva', 'Tiryan'}

    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'nakshatra_mukha' in out3['days'][0]
    assert out3['days'][0]['nakshatra_mukha'] in {'Adho', 'Urdhva', 'Tiryan'}

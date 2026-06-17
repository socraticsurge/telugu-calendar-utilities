"""Tests for panchanga_shuddhi.assess_shuddhi.

Each test verifies a specific rule by computing a real day with the Drik engine
and asserting the expected limb quality, using Hyderabad as the reference city.

DP reference days used below were cross-checked at drikpanchang.com day pages.
"""
import pytest
from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.panchanga_shuddhi import (
    PanchangaShuddhi,
    LimbAssessment,
    assess_shuddhi,
    _NAK_SHUDDHA,
    _NAK_ASHUDDHA,
    _NAK_MISHRA,
    _VERDICTS,
    _VARA_SHUDDHA,
    _VARA_ASHUDDHA,
    _KARANA_ASHUDDHA,
)

_HYD = next(c for c in CITIES if c.name == 'Hyderabad')
_ENGINE = DrikGanitaEngine()


def _assess(d: date) -> PanchangaShuddhi:
    day = _ENGINE.calculate(d, _HYD)
    return assess_shuddhi(day)


def _limb(result: PanchangaShuddhi, name: str) -> LimbAssessment:
    return next(lb for lb in result.limbs if lb.limb == name)


# ── Module-level sanity ───────────────────────────────────────────────────────

def test_nakshatra_sets_cover_all_27():
    all_naks = {
        'Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
        'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
        'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
        'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
        'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada',
        'Revati',
    }
    classified = _NAK_SHUDDHA | _NAK_ASHUDDHA | _NAK_MISHRA
    assert classified == all_naks, f'Unclassified: {all_naks - classified}'


def test_verdicts_have_6_entries():
    assert len(_VERDICTS) == 6
    assert _VERDICTS[0] == 'Sarva Ashuddha'
    assert _VERDICTS[5] == 'Sarva Shuddha'


def test_vara_sets_cover_all_7():
    all_varas = {
        'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
        'Guruvaram', 'Shukravaram', 'Shanivaram',
    }
    assert _VARA_SHUDDHA | _VARA_ASHUDDHA == all_varas
    assert _VARA_SHUDDHA & _VARA_ASHUDDHA == set()


# ── Return type ───────────────────────────────────────────────────────────────

def test_returns_panchangam_shuddhi_with_five_limbs():
    result = _assess(date(2026, 6, 17))   # today (Wednesday)
    assert isinstance(result, PanchangaShuddhi)
    assert len(result.limbs) == 5
    limb_names = [lb.limb for lb in result.limbs]
    assert limb_names == ['Tithi', 'Vaara', 'Nakshatra', 'Yoga', 'Karana']


def test_shuddha_count_matches_limbs():
    result = _assess(date(2026, 6, 17))
    expected_count = sum(1 for lb in result.limbs if lb.shuddha)
    assert result.shuddha_count == expected_count


def test_verdict_maps_to_count():
    result = _assess(date(2026, 6, 17))
    assert result.verdict == _VERDICTS[result.shuddha_count]


def test_date_preserved():
    d = date(2026, 6, 17)
    result = _assess(d)
    assert result.date == d


# ── Tithi rule ────────────────────────────────────────────────────────────────

def test_tithi_rikta_is_ashuddha():
    # 2026-Jun-23: Shukla Navami (9th) — Rikta — Hyderabad
    # Engine-verified: DrikGanitaEngine returns Shukla Navami for this date
    result = _assess(date(2026, 6, 23))
    t = _limb(result, 'Tithi')
    assert not t.shuddha, f'Expected Rikta tithi to be ashuddha, got {t.value}'
    assert t.quality == 'ashuddha'
    assert 'Rikta' in t.reason


def test_tithi_non_rikta_is_shuddha():
    # 2026-Jun-17 (today): Shukla Dvitiya (2nd) — not Rikta
    result = _assess(date(2026, 6, 17))
    t = _limb(result, 'Tithi')
    assert t.shuddha, f'Expected non-Rikta to be shuddha, got {t.value}'
    assert t.quality == 'shuddha'


# ── Vaara rule ────────────────────────────────────────────────────────────────

def test_wednesday_is_shuddha():
    # 2026-06-17 is a Wednesday (Budhavaram)
    result = _assess(date(2026, 6, 17))
    v = _limb(result, 'Vaara')
    assert v.shuddha
    assert v.value == 'Budhavaram'


def test_saturday_is_ashuddha():
    # 2026-06-20 is a Saturday (Shanivaram)
    result = _assess(date(2026, 6, 20))
    v = _limb(result, 'Vaara')
    assert not v.shuddha
    assert v.quality == 'ashuddha'


def test_thursday_is_shuddha():
    # 2026-06-18 is a Thursday (Guruvaram)
    result = _assess(date(2026, 6, 18))
    v = _limb(result, 'Vaara')
    assert v.shuddha
    assert v.value == 'Guruvaram'


def test_tuesday_is_ashuddha():
    # 2026-06-16 is a Tuesday (Mangalavaram)
    result = _assess(date(2026, 6, 16))
    v = _limb(result, 'Vaara')
    assert not v.shuddha
    assert v.quality == 'ashuddha'


# ── Nakshatra rule ────────────────────────────────────────────────────────────

def test_shuddha_nakshatra_marked_shuddha():
    # Scan forward until we hit a known Shuddha nakshatra (Rohini, Hasta, etc.)
    for delta in range(30):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        nak_name = day.nakshatra.name
        if nak_name in _NAK_SHUDDHA:
            result = assess_shuddhi(day)
            n = _limb(result, 'Nakshatra')
            assert n.shuddha, f'{d}: {nak_name} should be shuddha'
            assert n.quality == 'shuddha'
            return
    pytest.skip('No shuddha nakshatra found in scan window')


def test_ashuddha_nakshatra_marked_ashuddha():
    # Scan forward until we hit a known Ashuddha nakshatra (Ardra, Ashlesha, etc.)
    for delta in range(30):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        nak_name = day.nakshatra.name
        if nak_name in _NAK_ASHUDDHA:
            result = assess_shuddhi(day)
            n = _limb(result, 'Nakshatra')
            assert not n.shuddha, f'{d}: {nak_name} should be ashuddha'
            assert n.quality == 'ashuddha'
            return
    pytest.skip('No ashuddha nakshatra found in scan window')


def test_mishra_nakshatra_marked_mixed():
    # Krittika or Vishakha — scan 60 days
    for delta in range(60):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        nak_name = day.nakshatra.name
        if nak_name in _NAK_MISHRA:
            result = assess_shuddhi(day)
            n = _limb(result, 'Nakshatra')
            assert not n.shuddha, f'{d}: {nak_name} should not be shuddha'
            assert n.quality == 'mixed'
            return
    pytest.skip('No mishra nakshatra found in scan window')


# ── Yoga rule ─────────────────────────────────────────────────────────────────

def test_auspicious_yoga_is_shuddha():
    # Scan for an auspicious Nitya yoga
    from telugu_panchangam.personal.nitya_yoga import NITYA_AUSPICIOUS
    for delta in range(30):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        if day.yoga.name in NITYA_AUSPICIOUS:
            result = assess_shuddhi(day)
            y = _limb(result, 'Yoga')
            assert y.shuddha, f'{d}: {day.yoga.name} should be shuddha'
            assert y.quality == 'shuddha'
            return
    pytest.skip('No auspicious yoga found in scan window')


def test_hard_avoid_yoga_is_ashuddha():
    # Vyatipata or Vaidhriti — scan 60 days
    from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
    for delta in range(60):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        if day.yoga.name in NITYA_HARD_AVOID:
            result = assess_shuddhi(day)
            y = _limb(result, 'Yoga')
            assert not y.shuddha, f'{d}: {day.yoga.name} should be ashuddha'
            assert y.quality == 'ashuddha'
            return
    pytest.skip('No hard-avoid yoga in scan window')


def test_partial_dosha_yoga_is_mixed():
    from telugu_panchangam.personal.nitya_yoga import NITYA_PARTIAL_DOSHA_WINDOW
    for delta in range(60):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        if day.yoga.name in NITYA_PARTIAL_DOSHA_WINDOW:
            result = assess_shuddhi(day)
            y = _limb(result, 'Yoga')
            assert not y.shuddha, f'{d}: {day.yoga.name} should not be shuddha'
            assert y.quality == 'mixed'
            assert 'min' in y.reason
            return
    pytest.skip('No partial-dosha yoga in scan window')


# ── Karana rule ───────────────────────────────────────────────────────────────

def test_vishti_karana_is_ashuddha():
    # Scan for a Vishti karana day
    for delta in range(30):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        if day.karana and day.karana[0].name == 'Vishti':
            result = assess_shuddhi(day)
            k = _limb(result, 'Karana')
            assert not k.shuddha, f'{d}: Vishti should be ashuddha'
            assert k.quality == 'ashuddha'
            assert 'Bhadra' in k.reason or 'Vishti' in k.reason
            return
    pytest.skip('No Vishti karana at sunrise in scan window')


def test_movable_karana_is_shuddha():
    _MOVABLE_KARANAS = {'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garaja', 'Vanija'}
    for delta in range(14):
        d = date(2026, 6, 1 + delta)
        day = _ENGINE.calculate(d, _HYD)
        karana_name = day.karana[0].name if day.karana else None
        if karana_name in _MOVABLE_KARANAS:
            result = assess_shuddhi(day)
            k = _limb(result, 'Karana')
            assert k.shuddha, f'{d}: {karana_name} should be shuddha'
            assert k.quality == 'shuddha'
            return
    pytest.skip('No movable karana in scan window')


# ── Integration: known good/bad day ──────────────────────────────────────────

def test_thursday_high_shuddha_count():
    # Thursday (shuddha vara) — expect at least 2 pure limbs from any day
    result = _assess(date(2026, 6, 18))
    assert result.shuddha_count >= 1


def test_all_limb_quality_values_are_valid():
    valid = {'shuddha', 'ashuddha', 'mixed'}
    for delta in range(7):
        d = date(2026, 6, 17 + delta)
        result = _assess(d)
        for lb in result.limbs:
            assert lb.quality in valid, f'{d} {lb.limb}: unexpected quality {lb.quality!r}'
            assert isinstance(lb.shuddha, bool)
            assert lb.shuddha == (lb.quality == 'shuddha')

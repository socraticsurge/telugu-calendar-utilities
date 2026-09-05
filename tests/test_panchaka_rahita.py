from datetime import date

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.panchaka import (
    evaluate_panchaka,
    get_panchaka_remainder,
    lagna_to_number,
    nakshatra_to_number,
    tithi_to_number,
    vaaram_to_number,
)


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


# ─── Tithi numbering ────────────────────────────────────────────────────────

def test_tithi_shukla_pratipat_is_1():
    assert tithi_to_number('Shukla Pratipat') == 1


def test_tithi_shukla_saptami_is_7():
    assert tithi_to_number('Shukla Saptami') == 7


def test_tithi_pournami_is_15():
    assert tithi_to_number('Pournami') == 15
    assert tithi_to_number('Shukla Pournami') == 15


def test_tithi_krishna_pratipat_is_16():
    assert tithi_to_number('Krishna Pratipat') == 16


def test_tithi_krishna_trayodashi_is_28():
    assert tithi_to_number('Krishna Trayodashi') == 28


def test_tithi_amavasya_is_30():
    assert tithi_to_number('Amavasya') == 30
    assert tithi_to_number('Krishna Amavasya') == 30


def test_tithi_invalid_raises():
    with pytest.raises(ValueError, match='Unrecognised tithi'):
        tithi_to_number('Foo Bar')


# ─── Vaaram numbering ───────────────────────────────────────────────────────

def test_vaaram_adivaram_is_1():
    assert vaaram_to_number('Adivaram') == 1


def test_vaaram_somavaram_is_2():
    assert vaaram_to_number('Somavaram') == 2


def test_vaaram_shanivaram_is_7():
    assert vaaram_to_number('Shanivaram') == 7


# ─── Nakshatra numbering ────────────────────────────────────────────────────

def test_nakshatra_ashvini_is_1():
    assert nakshatra_to_number('Ashvini') == 1


def test_nakshatra_revati_is_27():
    assert nakshatra_to_number('Revati') == 27


def test_nakshatra_krittika_is_3():
    assert nakshatra_to_number('Krittika') == 3


# ─── Lagna numbering ────────────────────────────────────────────────────────

def test_lagna_mesha_is_1():
    assert lagna_to_number('Mesha') == 1


def test_lagna_meena_is_12():
    assert lagna_to_number('Meena') == 12


def test_lagna_dhanu_is_9():
    # Codebase uses 'Dhanu' not 'Dhanus'
    assert lagna_to_number('Dhanu') == 9


def test_lagna_karka_is_4():
    # Codebase uses 'Karka' not 'Karkata'
    assert lagna_to_number('Karka') == 4


# ─── Remainder arithmetic ───────────────────────────────────────────────────

def test_remainder_mrityu():
    # 7 + 1 + 1 + 1 = 10 → 10 mod 9 = 1 (Mrityu)
    assert get_panchaka_remainder(7, 1, 1, 1) == 1


def test_remainder_zero_is_rahita():
    # 9 + 0 + 0 + 0 → 9 mod 9 = 0 (Rahita)
    assert get_panchaka_remainder(9, 0, 0, 0) == 0


def test_remainder_wraps_at_9():
    assert get_panchaka_remainder(9, 9, 9, 9) == 0


# ─── evaluate_panchaka ──────────────────────────────────────────────────────

def test_evaluate_mrityu():
    # Shukla Saptami=7, Adivaram=1, Ashvini=1, Mesha=1 → 10 mod 9 = 1 → Mrityu
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Mesha')
    assert info.remainder == 1
    assert info.name == 'Mrityu'
    assert info.auspicious is False
    assert 'wedding' in info.avoid_for
    assert 'ceremony' in info.avoid_for


def test_evaluate_rahita_remainder_0():
    # Shukla Pratipat=1, Adivaram=1, Ashvini=1, Makara=10 → 13 mod 9 = 4? No.
    # Let's get remainder 0: need sum div 9. 9+0+0+0 = 9 mod 9 = 0.
    # Shukla Navami=9, Adivaram=1, Ashvini=1, Mesha=1 → 12 mod 9 = 3.
    # To get 0: need sum = 9. Shukla Pratipat(1)+Adivaram(1)+Ashvini(1)+Dhanu(9) = 12 mod 9 = 3.
    # Try: Pournami(15)+Adivaram(1)+Ashvini(1)+Kumbha(11) = 28 mod 9 = 1. No.
    # Shukla Ashtami(8)+Adivaram(1)+Ashvini(1)+Mesha(1)=11 mod 9 = 2.
    # Try: Shukla Panchami(5)+Adivaram(1)+Ashvini(1)+Mesha(1)=8 → rem=8=Roga. No.
    # Shukla Ekadashi(11)+Somavaram(2)+Bharani(2)+Vrishabha(2) = 17 mod 9 = 8.
    # Amavasya(30)+Adivaram(1)+Ashvini(1)+Mesha(1)=33 mod 9=6=Chora.
    # Need sum % 9 = 0: sum must be 9,18,27...
    # Krishna Pratipat(16)+Adivaram(1)+Ashvini(1)+Kumbha(11)=29 mod 9 = 2.
    # Pournami(15)+Adivaram(1)+Ashvini(1)+Meena(12)=29 mod 9 = 2.
    # Shukla Saptami(7)+Adivaram(1)+Krittika(3)+Vrishabha(2)=13 mod 9=4.
    # Shukla Saptami(7)+Adivaram(1)+Ashvini(1)+Meena(12)=21 mod 9=3.
    # Try sum=18: Amavasya(30)? 30+1+1+4=36 mod 9=0. 30+Adivaram(1)+Ashvini(1)+Karka(4)=36.
    info = evaluate_panchaka('Amavasya', 'Adivaram', 'Ashvini', 'Karka')
    assert info.remainder == 0
    assert info.name == 'Rahita'
    assert info.auspicious is True
    assert info.avoid_for == []


def test_evaluate_rahita_remainder_3():
    # 7+1+1+3=12 mod 9=3 → Rahita
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Mithuna')
    assert info.remainder == 3
    assert info.name == 'Rahita'
    assert info.auspicious is True


def test_evaluate_agni():
    # Need remainder 2. 7+1+1+2=11 mod 9=2.
    # Shukla Saptami(7)+Adivaram(1)+Ashvini(1)+Vrishabha(2) = 11 mod 9 = 2 → Agni
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Vrishabha')
    assert info.remainder == 2
    assert info.name == 'Agni'
    assert info.auspicious is False
    assert 'construction' in info.avoid_for


def test_evaluate_raja():
    # Need remainder 4. 7+1+1+4=13 mod 9=4 → Raja
    # Shukla Saptami(7)+Adivaram(1)+Ashvini(1)+Karka(4) = 13 mod 9 = 4
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Karka')
    assert info.remainder == 4
    assert info.name == 'Raja'
    assert info.auspicious is False
    assert 'joining_service' in info.avoid_for


def test_evaluate_chora():
    # Need remainder 6. 7+1+1+6=15 mod 9=6 → Chora
    # Shukla Saptami(7)+Adivaram(1)+Ashvini(1)+Kanya(6) = 15 mod 9 = 6
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Kanya')
    assert info.remainder == 6
    assert info.name == 'Chora'
    assert info.auspicious is False
    assert 'travel' in info.avoid_for


def test_evaluate_roga():
    # Need remainder 8. 7+1+1+8=17 mod 9=8 → Roga
    # Shukla Saptami(7)+Adivaram(1)+Ashvini(1)+Vrischika(8) = 17 mod 9 = 8
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Vrischika')
    assert info.remainder == 8
    assert info.name == 'Roga'
    assert info.auspicious is False
    assert 'surgery' in info.avoid_for


# ─── Engine populates panchaka_rahita ───────────────────────────────────────

def test_engine_populates_panchaka():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.panchaka_rahita is not None
    assert day.panchaka_rahita.remainder in range(9)
    assert day.panchaka_rahita.name in {'Rahita', 'Mrityu', 'Agni', 'Raja', 'Chora', 'Roga'}
    assert isinstance(day.panchaka_rahita.auspicious, bool)
    assert isinstance(day.panchaka_rahita.avoid_for, list)


def test_engine_panchaka_remainder_valid_range():
    """Panchaka remainder should always be 0..8 (mod 9)."""
    eng = DrikEngine()
    city = _hyderabad()
    for d in [date(2026, 1, 1), date(2026, 6, 15), date(2026, 12, 31)]:
        day = eng.calculate(d, city)
        assert day.panchaka_rahita is not None
        assert 0 <= day.panchaka_rahita.remainder <= 8


# ─── MCP tool serialization ─────────────────────────────────────────────────

def test_panchaka_in_all_mcp_tool_responses():
    import json

    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'panchaka_rahita' in out1
    assert out1['panchaka_rahita'] is not None
    assert 'name' in out1['panchaka_rahita']
    assert 'remainder' in out1['panchaka_rahita']
    assert 'auspicious' in out1['panchaka_rahita']
    assert 'avoid_for' in out1['panchaka_rahita']

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'panchaka_rahita' in out2
    assert out2['panchaka_rahita'] is not None

    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'panchaka_rahita' in out3['days'][0]
    assert out3['days'][0]['panchaka_rahita'] is not None


def test_panchaka_mcp_name_is_valid():
    import json

    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    valid_names = {'Rahita', 'Mrityu', 'Agni', 'Raja', 'Chora', 'Roga'}
    assert out['panchaka_rahita']['name'] in valid_names

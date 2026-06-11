# Daily Rasi Phalalu: deterministic text rendered from computed gochara,
# chandrabalam and (optionally) tarabalam facts — never free-form fiction.
from telugu_panchangam.personal.phalalu import rasi_phalalu, HOUSE_MEANINGS

# Jun 11 2026 sunrise sky (DP-verified rasis)
SKY = {
    'Surya': 'Vrishabha', 'Chandra': 'Meena', 'Kuja': 'Mesha',
    'Budha': 'Mithuna', 'Guru': 'Karka', 'Shukra': 'Karka',
    'Shani': 'Meena', 'Rahu': 'Kumbha', 'Ketu': 'Simha',
}


def test_house_meanings_cover_all_twelve():
    assert set(HOUSE_MEANINGS.keys()) == set(range(1, 13))


def test_structure_and_counts():
    out = rasi_phalalu('Mesha', SKY)
    assert out['janma_rasi'] == 'Mesha'
    assert out['favourable_count'] + out['blocked_count'] + out['adverse_count'] == 9
    assert isinstance(out['lines'], list) and len(out['lines']) >= 4
    assert out['day_quality'] in ('good', 'mixed', 'difficult')


def test_sade_sati_is_stated():
    out = rasi_phalalu('Mesha', SKY)
    assert any('Sade Sati' in l for l in out['lines'])


def test_moon_house_drives_day_quality():
    # Chandra in Meena: 12th from Mesha (avoid) vs 1st from Meena (good)
    assert rasi_phalalu('Mesha', SKY)['moon_house'] == 12
    assert rasi_phalalu('Meena', SKY)['moon_house'] == 1


def test_lines_are_traceable_to_verdicts():
    out = rasi_phalalu('Mesha', SKY)
    text = ' '.join(out['lines'])
    # Rahu favourable in the 11th -> gains house mentioned positively
    assert 'Rahu' in text and HOUSE_MEANINGS[11] in text
    # Shani 12th adverse -> expenses house mentioned
    assert HOUSE_MEANINGS[12] in text


def test_optional_tarabalam_line():
    out = rasi_phalalu('Meena', SKY, janma_nakshatra='Uttara Bhadrapada',
                       day_nakshatra='Revati')
    # U.Bh -> Revati = 2 Sampat
    assert any('Sampat' in l for l in out['lines'])
    out2 = rasi_phalalu('Meena', SKY)
    assert not any('tara' in l.lower() for l in out2['lines'])


def test_vedha_blocked_line_names_obstructor():
    sky = dict(SKY, **{'Surya': 'Kumbha', 'Kuja': 'Simha'})  # Dhanu: Surya 3rd blocked by Kuja
    out = rasi_phalalu('Dhanu', sky)
    assert any('vedha' in l.lower() and 'Kuja' in l for l in out['lines'])


def test_invalid_rasi_raises():
    import pytest
    with pytest.raises(ValueError):
        rasi_phalalu('Aries', SKY)


# --- MCP ---

def test_mcp_get_rasi_phalalu():
    import json
    from telugu_panchangam.mcp.tools import tool_get_rasi_phalalu
    result = json.loads(tool_get_rasi_phalalu('2026-06-11', 'Mesha', 'Hyderabad'))
    assert result['day_quality'] in ('good', 'mixed', 'difficult')
    assert any('Sade Sati' in l for l in result['lines'])
    assert 'disclaimer' in result

def test_mcp_get_rasi_phalalu_with_star():
    import json
    from telugu_panchangam.mcp.tools import tool_get_rasi_phalalu
    result = json.loads(tool_get_rasi_phalalu('2026-06-11', 'Meena', 'Hyderabad',
                                              janma_nakshatra='Uttara Bhadrapada'))
    assert any('Sampat' in l for l in result['lines'])

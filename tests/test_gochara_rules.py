# Gochara rules from Janma Rasi. Brihat Samhita 104.4 supports the seven
# classical favourable-house sets; Vedha, nodes and named Shani conditions
# have separate provenance states.
from telugu_panchangam.gochara.rules import (
    GOCHARA_FAVOURABLE, GOCHARA_PROVENANCE, VEDHA, gochara_for,
    named_conditions,
)


# --- The classical tables themselves ---

def test_favourable_houses_classical():
    assert GOCHARA_FAVOURABLE['Surya'] == frozenset({3, 6, 10, 11})
    assert GOCHARA_FAVOURABLE['Chandra'] == frozenset({1, 3, 6, 7, 10, 11})
    assert GOCHARA_FAVOURABLE['Kuja'] == frozenset({3, 6, 11})
    assert GOCHARA_FAVOURABLE['Budha'] == frozenset({2, 4, 6, 8, 10, 11})
    assert GOCHARA_FAVOURABLE['Guru'] == frozenset({2, 5, 7, 9, 11})
    assert GOCHARA_FAVOURABLE['Shukra'] == frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12})
    assert GOCHARA_FAVOURABLE['Shani'] == frozenset({3, 6, 11})
    # nodes follow the Shani convention
    assert GOCHARA_FAVOURABLE['Rahu'] == frozenset({3, 6, 11})
    assert GOCHARA_FAVOURABLE['Ketu'] == frozenset({3, 6, 11})


def test_gochara_layers_have_distinct_provenance_claims():
    assert GOCHARA_PROVENANCE == {
        'favourable_houses': 'gochara.favourable_houses',
        'vedha': 'gochara.vedha_tables',
        'nodes': 'gochara.nodes',
        'named_conditions': 'gochara.named_shani_conditions',
    }


def test_vedha_points_cover_every_favourable_house():
    for graha in ('Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani'):
        assert set(VEDHA[graha].keys()) == set(GOCHARA_FAVOURABLE[graha])


# --- Verdicts for a fixed sky (Jun 11 2026 sunrise, DP-verified rasis):
# Surya Vrishabha, Chandra Meena, Kuja Mesha, Budha Mithuna, Guru Karka,
# Shukra Karka, Shani Meena, Rahu Kumbha, Ketu Simha. ---

SKY = {
    'Surya': 'Vrishabha', 'Chandra': 'Meena', 'Kuja': 'Mesha',
    'Budha': 'Mithuna', 'Guru': 'Karka', 'Shukra': 'Karka',
    'Shani': 'Meena', 'Rahu': 'Kumbha', 'Ketu': 'Simha',
}


def _verdicts(janma_rasi):
    return {g['graha']: g for g in gochara_for(janma_rasi, SKY)}


def test_positions_counted_from_janma_rasi():
    v = _verdicts('Mesha')
    assert v['Surya']['position'] == 2     # Vrishabha is 2nd from Mesha
    assert v['Shani']['position'] == 12
    assert v['Guru']['position'] == 4
    assert v['Rahu']['position'] == 11


def test_verdicts_for_mesha():
    v = _verdicts('Mesha')
    assert v['Surya']['verdict'] == 'adverse'      # 2nd not favourable
    assert v['Guru']['verdict'] == 'adverse'       # 4th not favourable
    assert v['Rahu']['verdict'] == 'favourable'    # 11th, nodes cause/receive no vedha
    assert v['Shani']['verdict'] == 'adverse'      # 12th — sade sati territory


def test_vedha_blocks_favourable_transit():
    # For Vrishabha janma: Surya in Vrishabha is 1st (adverse), Budha in
    # Mithuna is 2nd (favourable; vedha point 5th = Kanya — empty, so clear).
    v = _verdicts('Vrishabha')
    assert v['Budha']['verdict'] == 'favourable'
    assert v['Budha']['vedha_by'] is None
    # For Makara janma: Shukra in Karka is 7th -> not in Shukra's favourable
    # set? 7 not in {1,2,3,4,5,8,9,11,12} -> adverse.
    assert _verdicts('Makara')['Shukra']['verdict'] == 'adverse'


def test_vedha_exemption_ravi_shani_and_chandra_budha():
    # Construct a sky where Shani sits on Surya's vedha point: for Dhanu
    # janma, Surya in Kumbha is 3rd (favourable, vedha point 9th = Simha).
    sky = dict(SKY, **{'Surya': 'Kumbha', 'Shani': 'Simha'})
    v = {g['graha']: g for g in gochara_for('Dhanu', sky)}
    # Shani at the vedha point does NOT obstruct Surya (father-son exemption)
    assert v['Surya']['verdict'] == 'favourable'
    # but Kuja at the same point would obstruct
    sky2 = dict(SKY, **{'Surya': 'Kumbha', 'Kuja': 'Simha'})
    v2 = {g['graha']: g for g in gochara_for('Dhanu', sky2)}
    assert v2['Surya']['verdict'] == 'blocked'
    assert v2['Surya']['vedha_by'] == 'Kuja'


# --- Named Shani conditions (Shani in Meena that day) ---

def test_sade_sati_phases():
    assert 'Sade Sati (rising phase)' in named_conditions('Mesha', SKY)    # 12th
    assert 'Sade Sati (peak phase)' in named_conditions('Meena', SKY)      # 1st
    assert 'Sade Sati (setting phase)' in named_conditions('Kumbha', SKY)  # 2nd

def test_ashtama_and_ardhastama_shani():
    assert 'Ashtama Shani' in named_conditions('Simha', SKY)        # 8th
    assert 'Ardhastama Shani' in named_conditions('Dhanu', SKY)     # 4th

def test_no_conditions_when_clear():
    assert named_conditions('Mithuna', SKY) == []   # Shani 10th from Mithuna


# --- MCP tool ---

def test_mcp_get_gochara():
    import json
    from telugu_panchangam.mcp.tools import tool_get_gochara
    result = json.loads(tool_get_gochara('2026-06-11', 'Mesha', 'Hyderabad'))
    assert result['janma_rasi'] == 'Mesha'
    assert 'Sade Sati (rising phase)' in result['conditions']
    v = {g['graha']: g for g in result['gochara']}
    assert v['Rahu']['verdict'] == 'favourable'
    assert v['Shani']['position_from_janma_rasi'] == 12
    assert len(result['gochara']) == 9
    assert result['provenance'] == GOCHARA_PROVENANCE
    assert '104.4 supports' in result['convention']
    assert 'open source-locator debt' in result['convention']


def test_mcp_get_gochara_validates():
    import json
    from telugu_panchangam.mcp.tools import tool_get_gochara
    assert 'error' in json.loads(tool_get_gochara('2026-06-11', 'Aries', 'Hyderabad'))

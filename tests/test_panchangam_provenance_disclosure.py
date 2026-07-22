"""Every Panchangam response category must disclose its authority state."""
import json
from pathlib import Path

import pytest

from telugu_panchangam.mcp.tools import (
    tool_get_muhurta,
    tool_get_panchangam,
    tool_get_panchangam_range,
)
from telugu_panchangam.panchangam_provenance import panchangam_provenance


ROOT = Path(__file__).parents[1]
IDENTITY_FIELDS = {'date', 'city', 'system', 'ayanamsa', 'provenance'}


def _claims():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return {claim['id']: claim for claim in ledger['claims']}


@pytest.mark.parametrize('system', ['drik', 'surya_siddhanta', 'vakya'])
def test_panchangam_provenance_claims_resolve_with_matching_states(system):
    provenance = panchangam_provenance(system)
    claims = _claims()
    groups = provenance['coverage_groups']

    assert provenance['schema_version'] == 1
    assert provenance['surface'] == 'panchangam'
    assert provenance['calculation_system'] == system
    assert len({group['id'] for group in groups}) == len(groups)
    for group in groups:
        claim = claims[group['claim_id']]
        assert claim['surface'] == 'panchangam'
        assert claim['verification_state'] == group['state']
        assert group['fields']
        assert group['note'].strip()


@pytest.mark.parametrize('system', ['drik', 'surya_siddhanta', 'vakya'])
def test_mcp_panchangam_disclosure_covers_every_output_category(system):
    result = json.loads(tool_get_panchangam(
        '2026-06-17', city='Hyderabad', system=system))
    provenance = result['provenance']
    covered = [
        field
        for group in provenance['coverage_groups']
        for field in group['fields']
    ]

    assert len(covered) == len(set(covered))
    assert set(covered) == set(result) - IDENTITY_FIELDS
    if system == 'drik':
        assert provenance['coverage_groups'][0]['claim_id'] == 'drik.sidereal_positions'
    else:
        assert provenance['coverage_groups'][0]['claim_id'] == 'panchangam.non_drik_engine_outputs'


def test_compact_panchangam_surfaces_keep_the_same_disclosure():
    expected = panchangam_provenance('drik')
    muhurta = json.loads(tool_get_muhurta(
        '2026-06-17', city='Hyderabad', system='drik'))
    date_range = json.loads(tool_get_panchangam_range(
        '2026-06-17', '2026-06-18', city='Hyderabad', system='drik'))

    assert muhurta['provenance'] == expected
    assert date_range['provenance'] == expected


def test_verified_traditional_rules_are_not_hidden_in_umbrella_claims():
    groups = {
        group['id']: group for group in panchangam_provenance('drik')['coverage_groups']
    }

    assert groups['bhadra_subwindows']['state'] == 'verified'
    assert groups['sankramana_avoidance']['state'] == 'verified'
    assert groups['panchaka_rahita']['state'] == 'verified'
    assert groups['mixed_daily_windows']['state'] == 'partially_verified'
    assert groups['other_derived_traditional_classifications']['state'] == 'needs_locator'

import json
from copy import deepcopy
from pathlib import Path

from telugu_panchangam.personal.election_assessors.benefic_rasi import (
    BENEFIC_RASI_CONVENTION_ID,
    evaluate_benefic_rasi,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_benefic_rasi_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(case=None):
    chart = deepcopy(ORACLE['base_chart'])
    case = case or {}
    for planet in chart['planets']:
        planet.update(case.get('overrides', {}).get(planet['name'], {}))
    if removed := case.get('remove'):
        chart['planets'] = [p for p in chart['planets'] if p['name'] != removed]
    return chart


def test_all_twelve_rasis_use_their_resolved_classical_lord():
    assert ORACLE['convention_id'] == BENEFIC_RASI_CONVENTION_ID
    for case in ORACLE['rasi_cases']:
        outcome = evaluate_benefic_rasi(_chart(), case['rashi'])
        assert outcome.status == case['status'], case
        assert f"owned by {case['lord']}" in outcome.evidence[0]


def test_conditional_chandra_budha_and_invalid_facts_match_oracle():
    for case in ORACLE['nature_cases']:
        outcome = evaluate_benefic_rasi(_chart(case), case['rashi'])
        assert outcome.status == case['status'], case['id']

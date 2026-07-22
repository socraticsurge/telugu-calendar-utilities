"""Contract tests for Raman's limited jewelry-purchase instruction."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).resolve().parents[1]


def test_gold_profile_keeps_source_rule_separate_from_project_heuristics():
    rules = ACTIVITY_RULES['gold']
    assert rules['source_claim'] == 'muhurta.gold_jewelry.purchase'
    assert rules['manual_checks'] == [
        'Election chart: Surya and Chandra should be well situated and '
        'aspected; the cited passage leaves this as a chart judgment rather '
        'than a fixed weekday, Tithi, Nakshatra or Lagna list.',
    ]
    assert rules['prefer_choghadiya'] == ('Labh', 1)
    assert rules['prefer_tithi_class'] == 'Bhadra'
    assert rules['prefer_vara'] == ['Shukravaram', 'Guruvaram']
    assert rules['prefer_lagna_class'] == 'Sthira'


def test_mcp_and_browser_publish_same_gold_claim_and_manual_check():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='gold', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.gold_jewelry.purchase'
    assert profile['manual_checks'] == ACTIVITY_RULES['gold']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(
            encoding='utf-8'))
    exported = browser['rules']['gold']
    assert exported['source_claim'] == profile['source_claim']
    assert exported['manual_checks'] == profile['manual_checks']

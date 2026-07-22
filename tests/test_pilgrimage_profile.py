"""Contract tests for Raman's pilgrimage and incorporated journey rules."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).resolve().parents[1]


def test_pilgrimage_profile_matches_raman_chapter_xiv():
    rules = ACTIVITY_RULES['pilgrimage']
    assert rules['source_claim'] == 'muhurta.pilgrimage'
    assert rules['skip_on_combust'] == ['Guru']
    assert rules['avoid_tithi_numbers'] == [14, 15]
    assert rules['prefer_nakshatras'] == [
        'Mrigashira', 'Ashwini', 'Pushya', 'Punarvasu', 'Hasta',
        'Anuradha', 'Shravana', 'Moola', 'Dhanishtha', 'Revati',
    ]
    assert rules['manual_checks'] == [
        'Election chart: place Guru in Lagna or the 9th house, as required '
        'by the pilgrimage-specific passage.',
    ]
    assert rules['prefer_lagna_class'] == 'Chara'


def test_mcp_and_browser_publish_same_pilgrimage_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='pilgrimage', city='Hyderabad'))
    profile = result['activity_profile']
    rules = ACTIVITY_RULES['pilgrimage']
    assert profile['source_claim'] == 'muhurta.pilgrimage'
    assert profile['automated_constraints']['skip_on_combust'] == ['Guru']
    assert profile['automated_constraints']['avoid_tithi_numbers'] == [14, 15]
    assert profile['automated_constraints']['prefer_nakshatras'] == \
        rules['prefer_nakshatras']
    assert profile['manual_checks'] == rules['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(
            encoding='utf-8'))
    exported = browser['rules']['pilgrimage']
    assert exported['source_claim'] == profile['source_claim']
    assert exported['skip_on_combust'] == ['Guru']
    assert exported['avoid_tithi_numbers'] == [14, 15]
    assert exported['prefer_nakshatras'] == rules['prefer_nakshatras']

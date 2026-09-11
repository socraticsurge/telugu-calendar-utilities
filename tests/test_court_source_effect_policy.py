"""Court source wording, interpretation, effects, and disclosures stay separate."""

import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import (
    ACTIVITY_RULES,
    COURT_SOURCE_EFFECT_POLICY,
)

ROOT = Path(__file__).parents[1]


def test_tithi_shorthand_records_all_source_candidates_without_blending():
    policy = COURT_SOURCE_EFFECT_POLICY["tithi_shorthand"]

    assert policy["source_wording"] == "Avoid the usual unfavorable Tithis."
    assert policy["source_candidates"] == [
        {
            "id": "raman-general-hints-p6",
            "locator": (
                "Chapter II, General hints, internal printed p. 6 (physical PDF p. 9)"
            ),
            "avoid_tithi_numbers": [4, 8, 12, 14],
        },
        {
            "id": "raman-panchanga-suddhi-p12",
            "locator": (
                "Chapter V, Panchang Suddhi, internal printed p. 12 "
                "(physical PDF p. 15)"
            ),
            "avoid_tithi_numbers": [4, 6, 8, 12, 14, 15],
        },
        {
            "id": "raman-namakarana-p22",
            "locator": (
                "Chapter VIII, Naming the child (Namakarana), internal "
                "printed p. 22 (physical PDF p. 25)"
            ),
            "avoid_tithi_numbers": [4, 6, 8, 9, 12, 14, 15],
        },
    ]


def test_current_navami_rejection_is_disclosed_as_policy_not_source_wording():
    selection = COURT_SOURCE_EFFECT_POLICY["tithi_shorthand"]["selection"]

    assert selection == {
        "id": "court-tithi-operational-policy-v1",
        "status": "selected_project_policy",
        "avoid_tithi_numbers": [4, 6, 8, 9, 12, 14, 15],
        "behavior_change": False,
        "claim_id": "muhurta.court.tithi_operational_policy_v1",
    }
    assert (
        ACTIVITY_RULES["court"]["avoid_tithi_numbers"]
        == selection["avoid_tithi_numbers"]
    )


def test_court_policy_separates_effects_baseline_scope_and_safety():
    assert COURT_SOURCE_EFFECT_POLICY["general_baseline"] == {
        "mode": "none",
        "claim_id": "muhurta.court.general_baseline_none_v1",
    }
    assert COURT_SOURCE_EFFECT_POLICY["atomic_rule_effects"] == {
        "court.mesha-lagna-or-navamsa": "reject",
        "court.guru-trikona": "prefer",
        "court.house-6-without-natural-malefic": "reject",
        "court.lagna-sixth-lords-max-separated": "prefer",
        "court.peace-benefic-pattern": "inform",
    }
    assert COURT_SOURCE_EFFECT_POLICY["upstream_product_policy"] == [
        "Tarabalam",
        "Chandrabalam",
        "Muhurta nature",
        "Choghadiya",
        "Nitya Yoga",
        "Anandadi",
        "personal Lagna fit",
        "Panchaka",
    ]
    assert COURT_SOURCE_EFFECT_POLICY["scope"]["affects_chart_completion"] is False
    assert (
        COURT_SOURCE_EFFECT_POLICY["legal_safety"]["affects_chart_completion"] is False
    )


def test_python_and_browser_export_the_same_policy():
    assert ACTIVITY_RULES["court"]["court_policy"] == COURT_SOURCE_EFFECT_POLICY

    browser = json.loads(
        (ROOT / "src/data/activity-rules.generated.json").read_text(encoding="utf-8")
    )
    assert browser["rules"]["court"]["court_policy"] == COURT_SOURCE_EFFECT_POLICY
    assert "court_policy" in browser["consumed_fields"]

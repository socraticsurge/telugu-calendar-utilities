"""Regression contract for the mutable literals centralized in issue #482."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CONSTANTS = {
    "telugu_panchangam/cities.py": {
        "_INDIA_TIMEZONE": "Asia/Kolkata",
    },
    "telugu_panchangam/mcp/tools.py": {
        "_CALCULATION_FAILED_ERROR": (
            "Calculation failed. Please check your inputs and try again."
        ),
        "_DATE_RANGE_LIMIT_ERROR": (
            "Date range exceeds 366-day limit. Use multiple calls for longer spans."
        ),
        "_END_DATE_ORDER_ERROR": "end_date must be >= start_date.",
        "_TOOL_CALL_FAILED_LOG": "tool call failed",
    },
    "telugu_panchangam/personal/activity_rules.py": {
        "_CLAIM_PURCHASE_GENERAL": "muhurta.purchase.general",
        "_NAKSHATRA_UTTARA_ASHADHA": "Uttara Ashadha",
        "_NAKSHATRA_UTTARA_BHADRAPADA": "Uttara Bhadrapada",
        "_NAKSHATRA_UTTARA_PHALGUNI": "Uttara Phalguni",
        "_TITHI_KRISHNA_DASHAMI": "Krishna Dashami",
        "_TITHI_KRISHNA_DWITIYA": "Krishna Dwitiya",
        "_TITHI_KRISHNA_PRATIPAT": "Krishna Pratipat",
        "_TITHI_KRISHNA_TRITIYA": "Krishna Tritiya",
        "_TITHI_SHUKLA_DASHAMI": "Shukla Dashami",
        "_TITHI_SHUKLA_DWITIYA": "Shukla Dwitiya",
        "_TITHI_SHUKLA_EKADASHI": "Shukla Ekadashi",
        "_TITHI_SHUKLA_PANCHAMI": "Shukla Panchami",
        "_TITHI_SHUKLA_PRATIPAT": "Shukla Pratipat",
        "_TITHI_SHUKLA_SAPTAMI": "Shukla Saptami",
        "_TITHI_SHUKLA_TRAYODASHI": "Shukla Trayodashi",
        "_TITHI_SHUKLA_TRITIYA": "Shukla Tritiya",
    },
    "telugu_panchangam/personal/election_chart_rules.py": {
        "_CLAIM_ANNAPRASANA_CHART": (
            "muhurta.annaprasana.raman_transcription_chart"
        ),
        "_CLAIM_GOLD_PURCHASE": "muhurta.gold_jewelry.purchase",
        "_CLAIM_LAND_PURCHASE": "muhurta.land_purchase.building",
        "_CLAIM_PURCHASE_GENERAL": "muhurta.purchase.general",
        "_CLAIM_SEEMANTHA": "muhurta.seemantha",
        "_CLAIM_SHANTIKA_PAUSHTIKA": "muhurta.shantika_paushtika",
        "_CLAIM_WEDDING": "muhurta.wedding",
        "_EIGHTH_HOUSE_VACANT": "8th house is vacant",
        "_GOLD_QUALIFICATION_POLICY": (
            "election_chart.gold_qualification_policy_v1"
        ),
        "_KUJA_OUTSIDE_EIGHTH": "Mangala (Kuja) is outside the 8th house",
    },
    "telugu_panchangam/personal/muhurta.py": {
        "_ADHIKA_PREFIX": "Adhika ",
    },
    "telugu_panchangam/personal/slot_scorers.py": {
        "_AMRITA_SIDDHI_YOGA": "Amrita Siddhi Yoga",
        "_SARVARTHA_SIDDHI_YOGA": "Sarvartha Siddhi Yoga",
    },
    "telugu_panchangam/special_yogas.py": {
        "_NAKSHATRA_UTTARA_ASHADHA": "Uttara Ashadha",
        "_NAKSHATRA_UTTARA_PHALGUNI": "Uttara Phalguni",
    },
    "tools/check_documentation_freshness.py": {
        "_FEED_DIMENSIONS_LABEL": "feed dimensions",
        "_MCP_TOOL_COUNT_LABEL": "MCP tool count",
        "_PYPI_README_PATH": "README_PYPI.md",
    },
    "tools/export_muhurtam_rule_crosswalk.py": {
        "_ACTIVITY_RULES_PATH": "telugu_panchangam/personal/activity_rules.py",
        "_MANUAL_DISPLAY_ROW": "manual.display-row",
        "_PANCHANGAM_PREDICATE_PREFIX": "panchangam.",
        "_PREDICATE_DAY_ADMISSION": "panchangam.day-admission",
        "_PREDICATE_DAY_EXCLUSION": "panchangam.day-exclusion",
        "_PREDICATE_RANKING_PREFERENCE": "panchangam.ranking-preference",
        "_PREDICATE_SLOT_ADMISSION": "panchangam.slot-admission",
        "_PREDICATE_SLOT_EXCLUSION": "panchangam.slot-exclusion",
        "_PRODUCT_SAFETY_POLICY_CLAIM": (
            "muhurta.product_safety_and_routing_policy"
        ),
    },
}


def _string_assignments(tree: ast.Module) -> dict[str, str]:
    return {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }


def test_sonar_flagged_mutable_literals_have_one_named_definition_each():
    assert sum(len(constants) for constants in EXPECTED_CONSTANTS.values()) == 48

    for relative_path, expected in EXPECTED_CONSTANTS.items():
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        assignments = _string_assignments(tree)
        assert {name: assignments.get(name) for name in expected} == expected

        literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        assert {value: literals.count(value) for value in expected.values()} == {
            value: 1 for value in expected.values()
        }

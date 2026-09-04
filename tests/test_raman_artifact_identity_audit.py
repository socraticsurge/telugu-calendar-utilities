"""Canonical contract for story #366's Raman identity migration."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/raman-artifact-identity-audit-v1.json"
PROVENANCE_PATH = ROOT / "docs/reference/provenance.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sources() -> dict[str, dict]:
    return {
        row["id"]: row
        for row in _load(PROVENANCE_PATH)["sources"]
    }


def _without_source_metadata(value):
    if isinstance(value, dict):
        return {
            key: _without_source_metadata(item)
            for key, item in value.items()
            if key not in {"source_ids", "source_locator"}
        }
    if isinstance(value, list):
        return [_without_source_metadata(item) for item in value]
    return value


def _semantic_sha256(path: Path) -> str:
    normalized = _without_source_metadata(_load(path))
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_work_and_inspected_derivative_are_distinct_canonical_objects() -> None:
    fixture = _load(FIXTURE_PATH)
    sources = _sources()
    work = sources["BVR-MUHURTHA-1993"]
    artifact = sources["BVR-MUHURTHA-CHISTABO-2020"]

    assert fixture["bibliographic_work"]["catalogued_page_count"] == 181
    assert work["inspected_directly"] is False
    assert work["url"].startswith("https://books.google.com/")
    assert fixture["bibliographic_work"]["catalogue_urls"] == work["catalogue_urls"]

    assert artifact["related_work_id"] == work["id"]
    assert artifact["inspected_directly"] is True
    assert artifact["exact_edition_match_verified"] is False
    assert artifact["physical_pdf_page_count"] == 78
    assert artifact["sha256"] == (
        "b8b878a444a487c83810329fdf8f057c40e92221a867db480d864da8be21a133"
    )
    assert artifact["byte_size"] == 2172882
    assert artifact["url"].endswith("/2020/06/Muhurta_Raman.pdf")
    assert fixture["inspected_artifact"]["sha256"] == artifact["sha256"]


def test_editorial_notice_and_two_offset_page_model_are_pinned() -> None:
    fixture = _load(FIXTURE_PATH)
    artifact = _sources()["BVR-MUHURTHA-CHISTABO-2020"]

    assert artifact["editorial_notice"] == {
        "physical_pdf_page": 3,
        "internal_folio": "II",
        "editor": "Simon aka Chistabo",
        "declares_re_edit": True,
        "declares_bracketed_additions": True,
        "declares_typo_corrections": True,
        "declares_appendix_omission": True,
    }
    assert artifact["pdf_metadata"] == {
        "title": "Muhurta-Raman Eng",
        "creator": "Word",
        "producer": "Mac OS X 10.13.6 Quartz PDFContext",
        "created_ist": "2020-06-17T16:29:55+05:30",
        "modified_ist": "2020-06-17T16:29:55+05:30",
        "pdf_version": "1.4",
    }
    assert fixture["page_numbering"]["segments"] == [
        {
            "physical_start": 4,
            "physical_end": 36,
            "internal_start": 1,
            "internal_end": 33,
            "relation": "internal = physical - 3",
        },
        {
            "physical_start": 37,
            "physical_end": 37,
            "internal_start": None,
            "internal_end": None,
            "relation": "unnumbered interstitial",
        },
        {
            "physical_start": 38,
            "physical_end": 78,
            "internal_start": 34,
            "internal_end": 74,
            "relation": "internal = physical - 4",
        },
    ]
    assert artifact["page_numbering"] == [
        {
            "physical_pdf_pages": "4-36",
            "internal_printed_pages": "1-33",
            "relation": "internal = physical - 3",
        },
        {
            "physical_pdf_pages": "37",
            "internal_printed_pages": None,
            "relation": "unnumbered interstitial",
        },
        {
            "physical_pdf_pages": "38-78",
            "internal_printed_pages": "34-74",
            "relation": "internal = physical - 4",
        },
    ]


def test_every_active_raman_claim_matches_the_revalidated_audit() -> None:
    fixture = _load(FIXTURE_PATH)
    provenance = _load(PROVENANCE_PATH)
    current_claims = {
        claim["id"]: claim
        for claim in provenance["claims"]
        if "BVR-MUHURTHA-1993" in claim.get("source_ids", [])
    }
    audited = {row["claim_id"]: row for row in fixture["claim_audit"]}

    assert len(current_claims) == 34
    assert audited.keys() == current_claims.keys()
    for claim_id, row in audited.items():
        claim = current_claims[claim_id]
        assert row["verification_state"] == claim["verification_state"]
        assert row["verified_locator"] == (claim.get("locator") or "")
        assert row["canonical_source_ids"] == claim["source_ids"]


def test_migration_corrects_17_locators_without_inventing_four_missing_ones() -> None:
    fixture = _load(FIXTURE_PATH)
    rows = fixture["claim_audit"]
    counts = Counter(row["audit_state"] for row in rows)

    assert counts == {"aligned": 13, "correction_required": 17, "no_locator": 4}
    assert fixture["counts"] == {
        "total_source_linked_claims": 34,
        "aligned": 13,
        "correction_required": 17,
        "no_locator": 4,
    }
    for row in rows:
        if row["audit_state"] == "correction_required":
            assert row["page_coordinates_changed"] is True
            assert row["pre_migration_locator"] != row["verified_locator"]
        elif row["audit_state"] == "no_locator":
            assert row["page_coordinates_changed"] is False
            assert row["verification_state"] == "needs_locator"
            assert row["pre_migration_locator"] == row["verified_locator"] == ""
            assert "BVR-MUHURTHA-CHISTABO-2020" not in row["canonical_source_ids"]
        else:
            # Page coordinates were already aligned, but the locator text is
            # still canonicalized to name the inspected artifact and both
            # pagination systems explicitly.
            assert row["page_coordinates_changed"] is False
            assert row["pre_migration_locator"]
            assert row["verified_locator"]


def test_every_located_raman_claim_names_both_page_systems_and_artifact() -> None:
    fixture = _load(FIXTURE_PATH)
    for row in fixture["claim_audit"]:
        if row["audit_state"] == "no_locator":
            continue
        locator = row["verified_locator"]
        assert "2020 Chistabo derivative" in locator
        assert "internal printed p" in locator
        assert "physical PDF p" in locator
        assert row["canonical_source_ids"][:2] == [
            "BVR-MUHURTHA-1993",
            "BVR-MUHURTHA-CHISTABO-2020",
        ]


def test_vehicle_and_post_interstitial_corrections_are_exact() -> None:
    rows = {
        row["claim_id"]: row
        for row in _load(FIXTURE_PATH)["claim_audit"]
    }
    assert "internal printed p. 11 (physical PDF p. 14)" in (
        rows["muhurta.vehicle.acquisition"]["verified_locator"]
    )
    for claim_id in (
        "muhurta.house_purchase.completed",
        "muhurta.land_purchase.building",
    ):
        assert "internal printed p. 54 (physical PDF p. 58)" in (
            rows[claim_id]["verified_locator"]
        )
    assert "internal printed pp. 54-55 (physical PDF pp. 58-59)" in (
        rows["muhurta.home_repair.commencement"]["verified_locator"]
    )


def test_provenance_only_release_preserves_rule_and_scoring_artifacts() -> None:
    fixture = _load(FIXTURE_PATH)
    expected_rules = fixture["protected_rule_semantics_sha256"]
    actual_rules = {
        relative: _semantic_sha256(ROOT / relative)
        for relative in expected_rules
    }
    assert actual_rules == expected_rules

    expected_scorers = fixture["protected_scoring_implementation_sha256"]
    actual_scorers = {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in expected_scorers
    }
    assert actual_scorers == expected_scorers


def test_report_records_completed_migration_and_remaining_evidence_boundary() -> None:
    report = (
        ROOT
        / "docs/research/election-chart-automation/raman-artifact-identity-audit/report.md"
    ).read_text(encoding="utf-8")
    assert "release candidate" in report
    assert "no scan of the 181-page 1993 edition was inspected" in report.lower()
    assert "Non-source rule semantics remain unchanged" in report
    assert "scoring implementations remain byte-identical" in report

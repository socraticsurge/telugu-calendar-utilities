"""Canonical contract for story #366's Raman identity migration."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/raman-artifact-identity-audit-v1.json"
CLAIM_BASELINE_PATH = (
    ROOT / "tests/fixtures/raman-artifact-identity-claims-v1.15.2.json"
)
SUCCESSOR_AUDIT_DIR = ROOT / "tests/fixtures/raman-successor-audits"
PROVENANCE_PATH = ROOT / "docs/reference/provenance.json"
BASELINE_RELEASE = "1.15.2"
BASELINE_FIXTURE_SHA256 = (
    "f97c70ecd10f11da04f9c81edf11974e80ddf190a5e0dfddc76388ae781625fe"
)
CLAIM_BASELINE_SHA256 = (
    "cb5dc665209ce465055996745db0f32859179bfeffdda339a5a04106be6a1ed6"
)
RAMAN_WORK_ID = "BVR-MUHURTHA-1993"
RAMAN_ARTIFACT_ID = "BVR-MUHURTHA-CHISTABO-2020"
STRICT_SEMVER = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
)
MANIFEST_FILENAME = re.compile(
    rf"(?P<release>{STRICT_SEMVER.pattern})-"
    r"(?P<activity>[a-z0-9]+(?:-[a-z0-9]+)*)\.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_immutable_baseline_fixture() -> None:
    assert hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest() == (
        BASELINE_FIXTURE_SHA256
    )
    assert hashlib.sha256(CLAIM_BASELINE_PATH.read_bytes()).hexdigest() == (
        CLAIM_BASELINE_SHA256
    )


def _release_key(release: str) -> tuple[int, ...]:
    match = STRICT_SEMVER.fullmatch(release)
    assert match is not None
    return tuple(int(match.group(name)) for name in ("major", "minor", "patch"))


def _project_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project]" in pyproject
    project_block = pyproject.split("[project]", 1)[1].split("\n[", 1)[0]
    matches = re.findall(r'^version\s*=\s*"([^"]+)"\s*$', project_block, re.MULTILINE)
    assert len(matches) == 1
    _release_key(matches[0])
    return matches[0]


def _successor_manifests() -> list[dict]:
    records: list[tuple[tuple[int, ...], dict]] = []
    for path in SUCCESSOR_AUDIT_DIR.glob("*.json"):
        filename = MANIFEST_FILENAME.fullmatch(path.name)
        assert filename is not None
        manifest = _load(path)
        assert manifest["release"] == filename.group("release")
        assert manifest["activity"] == filename.group("activity")
        records.append((_release_key(manifest["release"]), manifest))
    assert records
    records.sort(key=lambda record: record[0])

    release_keys = [record[0] for record in records]
    assert len(release_keys) == len(set(release_keys))
    assert all(left < right for left, right in pairwise(release_keys))

    expected_parent = BASELINE_RELEASE
    manifests: list[dict] = []
    for release_key, manifest in records:
        assert manifest["schema_version"] == 1
        assert manifest["parent_release"] == expected_parent
        assert release_key > _release_key(manifest["parent_release"])
        assert manifest["baseline_fixture"] == (
            "tests/fixtures/raman-artifact-identity-audit-v1.json"
        )
        assert manifest["baseline_fixture_sha256"] == BASELINE_FIXTURE_SHA256
        manifests.append(manifest)
        expected_parent = manifest["release"]
    assert manifests[-1]["release"] == _project_version()
    return manifests


def _baseline_claim_hashes() -> dict[str, str]:
    baseline = _load(CLAIM_BASELINE_PATH)
    assert baseline["schema_version"] == 1
    assert baseline["release"] == BASELINE_RELEASE
    assert baseline["source_revision"] == ("c34d8eb42528a3dfbb341e3205cf60d4ce195ba9")
    assert baseline["source_path"] == "docs/reference/provenance.json"
    assert baseline["baseline_fixture"] == (
        "tests/fixtures/raman-artifact-identity-audit-v1.json"
    )
    assert baseline["baseline_fixture_sha256"] == BASELINE_FIXTURE_SHA256
    return baseline["claim_records_sha256"]


def _sources() -> dict[str, dict]:
    return {row["id"]: row for row in _load(PROVENANCE_PATH)["sources"]}


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


def _pointer_parts(pointer: str) -> tuple[str, ...]:
    assert pointer.startswith("/") and pointer != "/"
    return tuple(
        part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")
    )


def _pointer_parent(document: dict, pointer: str) -> tuple[dict, str]:
    parts = _pointer_parts(pointer)
    current: Any = document
    for part in parts[:-1]:
        assert isinstance(current, dict) and part in current
        current = current[part]
    assert isinstance(current, dict)
    return current, parts[-1]


def _assert_non_overlapping_pointers(manifest: dict) -> None:
    by_artifact: dict[str, list[tuple[str, ...]]] = {}
    for delta in manifest["semantic_deltas"]:
        activity = manifest["activity"]
        scope = delta["scope"]
        artifact = delta["artifact"]
        pointer = delta["json_pointer"]
        parts = _pointer_parts(pointer)

        if scope == f"{activity}_contract":
            assert artifact == "src/data/activity-rules.generated.json"
            assert pointer == f"/check_contract/activities/{activity}"
        elif scope == f"{activity}_activity_rules":
            assert artifact == "src/data/activity-rules.generated.json"
            assert pointer == f"/rules/{activity}"
        elif scope == f"{activity}_consumed_fields":
            assert artifact == "src/data/activity-rules.generated.json"
            assert pointer == "/consumed_fields"
        elif scope == f"{activity}_rules":
            assert artifact == "src/data/election-chart-rules.generated.json"
            assert pointer == f"/rules/{activity}"
        elif scope == f"{activity}_remainder":
            assert artifact == "src/data/election-chart-rules.generated.json"
            assert pointer == f"/manual_remainders/{activity}"
        elif scope == f"{activity}_convention":
            assert artifact == "src/data/election-chart-rules.generated.json"
            assert len(parts) == 2 and parts[0] == "conventions"
        elif scope == "shared_schema":
            assert artifact == "src/data/election-chart-rules.generated.json"
            assert pointer in {"/schema_version", "/convention_schema_version"}
        else:
            assert scope == "completion_registry"
            assert artifact == "src/data/election-chart-rules.generated.json"
            assert pointer == "/complete_assessors"

        by_artifact.setdefault(delta["artifact"], []).append(parts)

    for pointers in by_artifact.values():
        for index, left in enumerate(pointers):
            for right in pointers[index + 1 :]:
                shortest = min(len(left), len(right))
                assert left[:shortest] != right[:shortest], (
                    "A successor manifest may not declare duplicate or "
                    "ancestor/descendant JSON pointers"
                )


def _reverse_declared_rule_deltas(
    relative: str,
    manifests: list[dict],
) -> str:
    document = _without_source_metadata(_load(ROOT / relative))

    for manifest in reversed(manifests):
        _assert_non_overlapping_pointers(manifest)
        for delta in reversed(manifest["semantic_deltas"]):
            if delta["artifact"] != relative:
                continue
            parent, key = _pointer_parent(document, delta["json_pointer"])
            assert key in parent
            assert _json_sha256(parent[key]) == delta["after_sha256"]

            if delta["operation"] == "add":
                assert "before" not in delta and "before_sha256" not in delta
                del parent[key]
            else:
                assert delta["operation"] == "replace"
                before = deepcopy(delta["before"])
                assert _json_sha256(before) == delta["before_sha256"]
                parent[key] = before

    return _json_sha256(document)


def _reverse_declared_source_transforms(
    relative: str,
    manifests: list[dict],
) -> str:
    source = (ROOT / relative).read_bytes().decode("utf-8")
    for manifest in reversed(manifests):
        paths = [
            declaration["path"]
            for declaration in manifest["protected_source_transforms"]
        ]
        assert len(paths) == len(set(paths))
        for declaration in reversed(manifest["protected_source_transforms"]):
            if declaration["path"] != relative:
                continue
            assert declaration["scope"].startswith(f"{manifest['activity']}_")
            for transform in reversed(declaration["transforms"]):
                before = transform["before"]
                after = transform["after"]
                assert before != after
                assert source.count(after) == 1
                source = source.replace(after, before, 1)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


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
    _assert_immutable_baseline_fixture()
    fixture = _load(FIXTURE_PATH)
    provenance = _load(PROVENANCE_PATH)
    all_claims = {claim["id"]: claim for claim in provenance["claims"]}
    audited = {row["claim_id"]: row for row in fixture["claim_audit"]}
    baseline_claim_hashes = _baseline_claim_hashes()

    assert len(audited) == fixture["counts"]["total_source_linked_claims"] == 34
    assert set(baseline_claim_hashes) == set(audited)
    for claim_id, row in audited.items():
        assert claim_id in all_claims
        claim = all_claims[claim_id]
        assert row["verification_state"] == claim["verification_state"]
        assert row["verified_locator"] == (claim.get("locator") or "")
        assert row["canonical_source_ids"] == claim["source_ids"]

    manifests = _successor_manifests()
    expected_current_ids = set(audited)
    for manifest in manifests:
        release_claim_ids: set[str] = set()
        for expected in manifest["raman_claim_changes"]:
            claim_id = expected["claim_id"]
            assert claim_id not in release_claim_ids
            release_claim_ids.add(claim_id)

            relationship = expected["relationship"]
            if relationship == "successor_addition":
                assert claim_id not in expected_current_ids
                assert "before" not in expected and "before_sha256" not in expected
                expected_current_ids.add(claim_id)
            elif relationship == "baseline_context_extension":
                assert claim_id in audited
                assert "before" in expected and "before_sha256" in expected
            else:
                assert relationship == "successor_revision"
                assert claim_id in expected_current_ids
                assert "before" in expected and "before_sha256" in expected

    current_raman_claim_ids = {
        claim_id
        for claim_id, claim in all_claims.items()
        if RAMAN_WORK_ID in claim.get("source_ids", [])
    }
    derivative_claim_ids = {
        claim_id
        for claim_id, claim in all_claims.items()
        if RAMAN_ARTIFACT_ID in claim.get("source_ids", [])
    }
    assert derivative_claim_ids <= current_raman_claim_ids
    assert current_raman_claim_ids == expected_current_ids

    reconstructed_claims = {
        claim_id: deepcopy(all_claims[claim_id]) for claim_id in expected_current_ids
    }
    for manifest in reversed(manifests):
        for expected in reversed(manifest["raman_claim_changes"]):
            claim_id = expected["claim_id"]
            assert claim_id in reconstructed_claims
            claim = reconstructed_claims[claim_id]
            assert claim["verification_state"] == expected["verification_state"]
            assert expected["source_ids"][:2] == [RAMAN_WORK_ID, RAMAN_ARTIFACT_ID]
            assert claim["source_ids"] == expected["source_ids"]
            assert (claim.get("locator") or "") == expected["locator"]
            assert "2020 Chistabo derivative" in expected["locator"]
            assert "internal printed p" in expected["locator"]
            assert "physical PDF p" in expected["locator"]
            assert _json_sha256(claim) == expected["after_sha256"]

            if expected["relationship"] == "successor_addition":
                del reconstructed_claims[claim_id]
            else:
                before = deepcopy(expected["before"])
                assert before["id"] == claim_id
                assert _json_sha256(before) == expected["before_sha256"]
                reconstructed_claims[claim_id] = before

    assert set(reconstructed_claims) == set(audited)
    assert {
        claim_id: _json_sha256(claim)
        for claim_id, claim in reconstructed_claims.items()
    } == baseline_claim_hashes


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
    rows = {row["claim_id"]: row for row in _load(FIXTURE_PATH)["claim_audit"]}
    assert (
        "internal printed p. 11 (physical PDF p. 14)"
        in (rows["muhurta.vehicle.acquisition"]["verified_locator"])
    )
    for claim_id in (
        "muhurta.house_purchase.completed",
        "muhurta.land_purchase.building",
    ):
        assert (
            "internal printed p. 54 (physical PDF p. 58)"
            in (rows[claim_id]["verified_locator"])
        )
    assert (
        "internal printed pp. 54-55 (physical PDF pp. 58-59)"
        in (rows["muhurta.home_repair.commencement"]["verified_locator"])
    )


def test_provenance_only_release_preserves_rule_and_scoring_artifacts() -> None:
    _assert_immutable_baseline_fixture()
    fixture = _load(FIXTURE_PATH)
    manifests = _successor_manifests()

    expected_rules = fixture["protected_rule_semantics_sha256"]
    declared_rule_artifacts = {
        delta["artifact"]
        for manifest in manifests
        for delta in manifest["semantic_deltas"]
    }
    assert declared_rule_artifacts <= set(expected_rules)
    reconstructed_rules = {
        relative: _reverse_declared_rule_deltas(relative, manifests)
        for relative in expected_rules
    }
    assert reconstructed_rules == expected_rules

    expected_scorers = fixture["protected_scoring_implementation_sha256"]
    declared_source_paths = {
        declaration["path"]
        for manifest in manifests
        for declaration in manifest["protected_source_transforms"]
    }
    assert declared_source_paths <= set(expected_scorers)
    reconstructed_scorers = {
        relative: _reverse_declared_source_transforms(relative, manifests)
        for relative in expected_scorers
    }
    assert reconstructed_scorers == expected_scorers


def test_report_records_completed_migration_and_remaining_evidence_boundary() -> None:
    report = (
        ROOT
        / "docs/research/election-chart-automation/raman-artifact-identity-audit/report.md"
    ).read_text(encoding="utf-8")
    assert "release candidate" in report
    assert "no scan of the 181-page 1993 edition was inspected" in report.lower()
    assert "Non-source rule semantics remain unchanged" in report
    assert "scoring implementations remain byte-identical" in report

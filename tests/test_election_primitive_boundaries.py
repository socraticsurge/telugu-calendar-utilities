"""Stable ownership and compatibility contracts for election primitives."""

from pathlib import Path

from telugu_panchangam.personal.election_assessors import (
    chart_geometry,
    event_admission,
    facts,
    graha_nature,
    primitives,
)

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_python_primitive_exports_are_compatibility_aliases():
    assert primitives.evaluate_all_planets_in_houses is (
        chart_geometry.evaluate_all_planets_in_houses
    )
    assert primitives.navamsa_rashi is chart_geometry.navamsa_rashi
    assert primitives.evaluate_well_situated is chart_geometry.evaluate_well_situated
    assert primitives.evaluate_full_aspect is chart_geometry.evaluate_full_aspect
    assert primitives.gold_transition_uncertainty is (
        chart_geometry.gold_transition_uncertainty
    )
    assert primitives.evaluate_house_free_of_natural_malefics is (
        graha_nature.evaluate_house_free_of_natural_malefics
    )
    assert facts.PlanetPosition is event_admission.PlanetPosition
    assert facts.planet_positions is event_admission.planet_positions


def test_geometry_modules_do_not_import_source_or_event_policy():
    forbidden = (
        'activity_rules',
        'conventions',
        'election_chart_rules',
        'karnavedha',
    )
    for relative_path in (
        'telugu_panchangam/personal/election_assessors/chart_geometry.py',
        'src/scorer/election-assessors/chart-geometry.ts',
    ):
        source = (ROOT / relative_path).read_text(encoding='utf-8')
        assert all(name not in source for name in forbidden)


def test_mirrored_boundary_record_names_every_domain():
    architecture = (
        ROOT / 'telugu_panchangam' / 'personal' / 'election_assessors'
        / 'ARCHITECTURE.md'
    ).read_text(encoding='utf-8')

    for domain in (
        'chart geometry',
        'graha nature',
        'combustion',
        'conjunction',
        'Vedha',
        'event admission',
        'non-scoring event context',
    ):
        assert domain in architecture

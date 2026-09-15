"""Generation is checked by the existing full Python gate; no CI changes needed."""

from tools.export_shared_calendar_tables import ROOT, build_export, rendered


def test_shared_calendar_tables_are_current():
    assert (
        ROOT / "src/data/shared-calendar-tables.generated.json"
    ).read_text() == rendered()


def test_browser_projection_preserves_intentional_names_and_house_indexing():
    data = build_export()
    assert data["browserYogaNames"][1] == "Priti"
    assert data["browserYogaNames"][8] == "Shula"
    assert data["browserYogaNames"][17] == "Variyana"
    assert data["shaniConditions"][0] == "Sade Sati (peak phase)"
    assert data["shaniConditions"][11] == "Sade Sati (rising phase)"
    assert len(data["shaniConditions"]) == 12

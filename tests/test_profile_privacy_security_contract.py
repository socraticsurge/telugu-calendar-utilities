"""Static release guards for the browser profile privacy boundary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_profile_page_does_not_execute_third_party_analytics() -> None:
    landing = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "gc.zgo.at/count.js" not in landing
    assert "data-goatcounter" not in landing


def test_legacy_tarabalam_templates_escape_profile_names() -> None:
    panel = (ROOT / "src/panels/tarabalam.ts").read_text(encoding="utf-8")

    assert "days are favourable for ${htmlEsc(who)}" in panel
    assert "No favourable days for ${htmlEsc(who)} in this range, and none found" in panel
    assert "days are favourable for ${who}" not in panel
    assert "No favourable days for ${who} in this range, and none found" not in panel


def test_every_builtin_personal_share_omits_saved_profile_names() -> None:
    tarabalam = (ROOT / "src/panels/tarabalam.ts").read_text(encoding="utf-8")
    gochara = (ROOT / "src/panels/gochara.ts").read_text(encoding="utf-8")

    assert "profiles.map(pr => `${pr.name}: ${pr.nak}`).join(' · ')" not in tarabalam
    assert "Saved profile names and birth-star details are intentionally omitted" in tarabalam
    assert "lines.push(`${view.label} · ${ph.quality} day`);" not in gochara
    assert "lines.push(`${RASI_NAMES[jr]} Janma Rashi · ${ph.quality} day`);" in gochara

"""Compatibility guardrails for the browser-local guest-profile migration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_legacy_muhurta_writer_preserves_additive_profile_identity():
    source = _read('src/panels/tarabalam.ts')

    assert 'const existing = readLegacyGuestProfileRows(localStorage);' in source
    assert 'const row = mergeLegacyGuestProfileRow(previous, {' in source


def test_legacy_consumers_read_corrupt_storage_safely_and_escape_names():
    tarabalam = _read('src/panels/tarabalam.ts')
    gochara = _read('src/panels/gochara.ts')

    assert tarabalam.count('readLegacyGuestProfileRows(localStorage)') >= 3
    assert 'readLegacyGuestProfileRows(localStorage)' in gochara
    assert 'value="${htmlEsc(v.name || \'\')}"' in tarabalam
    assert "JSON.parse(localStorage.getItem('tc-tb-profiles')" not in tarabalam
    assert "JSON.parse(localStorage.getItem('tc-tb-profiles')" not in gochara

"""Browser smoke constants; no automatic test collection."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DIST_DIR = REPO_ROOT / 'dist'

MUHURTA_FIXTURE_DATE = '2026-06-11'

MUHURTA_FEED_FIXTURE = (
    REPO_ROOT / 'tests/fixtures/golden_hyderabad_drik_2026-06-11_3d.ics'
)

MUHURTA_PLANET_NAMES = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)

MUHURTA_PLANET_RASHIS = (
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha',
    'Kanya', 'Tula', 'Vrischika', 'Dhanu',
)

PRIVATE_TRAVELLER_ID = 'guest_private_traveller'

OTHER_TRAVELLER_ID = 'guest_other_traveller'

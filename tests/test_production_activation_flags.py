"""Release contract for public guest-calculation client activation."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_build_enables_both_guest_calculation_journeys():
    settings = {
        line.strip()
        for line in (ROOT / '.env.production').read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    }

    assert settings == {
        'VITE_BIRTH_PROFILE_API_ENABLED=true',
        'VITE_ELECTION_CHART_API_ENABLED=true',
    }

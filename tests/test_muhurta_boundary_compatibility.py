"""Frozen pre-extraction outputs, not independent astronomical verification."""

import hashlib
import inspect
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.personal import muhurta

FIXTURE_PATH = Path(__file__).parent / 'fixtures/muhurta-boundary-compatibility.json'
ENGINES = {
    'drik': DrikGanitaEngine,
    'surya_siddhanta': SuryaSiddhantaEngine,
    'vakya': VakyaEngine,
}
SCENARIOS = [
    ('drik', 'Hyderabad', '2026-07-18'),
    ('drik', 'London', '2026-03-29'),
    ('drik', 'London', '2026-10-25'),
    ('surya_siddhanta', 'Hyderabad', '2026-06-17'),
    ('vakya', 'Hyderabad', '2026-07-18'),
    ('surya_siddhanta', 'London', '2026-10-25'),
]
PUBLIC_FUNCTIONS = (
    'day_slots',
    'night_slots',
    'diagnose_day',
    'assign_tiers',
    'score_tier',
    'relative_tier',
    'karnavedha_daylight_assessment',
)


def scenario_digest(system, city_name, iso_date):
    engine = ENGINES[system]()
    city = next(item for item in CITIES if item.name == city_name)
    start = date.fromisoformat(iso_date)
    day = engine.calculate(start, city)
    next_day = engine.calculate(start + timedelta(days=1), city)
    outputs = []
    for activity in muhurta.ACTIVITIES:
        for mode in muhurta.CHANDRA_MODES:
            for slot_engine in (None, engine):
                options = {
                    'activity': activity,
                    'chandra_mode': mode,
                    'janma_nakshatras': ['Uttara Bhadrapada', 'Vishakha'],
                    'janma_rasis': ['Meena', None],
                    'travel_direction': 'South',
                }
                outputs.append(
                    {
                        'day': muhurta.day_slots(day, **options, engine=slot_engine),
                        'night': muhurta.night_slots(
                            day, next_day, **options, engine=slot_engine
                        ),
                        'diagnosis': muhurta.diagnose_day(day, **options),
                    }
                )
    encoded = json.dumps(
        outputs, ensure_ascii=False, default=lambda value: value.isoformat()
    ).encode()
    return {
        'sha256': hashlib.sha256(encoded).hexdigest(),
        'requests': len(outputs),
        'day_slots': sum(len(item['day']) for item in outputs),
        'night_slots': sum(len(item['night']) for item in outputs),
    }


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_all_activity_results_match_pre_extraction_baseline(scenario):
    fixture = json.loads(FIXTURE_PATH.read_text())
    assert scenario_digest(*scenario) == fixture['scenarios']['/'.join(scenario)]


def test_public_muhurta_signatures_stay_compatible():
    fixture = json.loads(FIXTURE_PATH.read_text())
    assert {
        name: str(inspect.signature(getattr(muhurta, name)))
        for name in PUBLIC_FUNCTIONS
    } == fixture['signatures']

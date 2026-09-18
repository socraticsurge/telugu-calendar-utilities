"""Public reason contract for independent Homahuti and Agnivasa gates."""
import json
from pathlib import Path

import pytest

from telugu_panchangam.personal.homa import homa_election

CASES = json.loads((Path(__file__).parent / 'fixtures/homa-election-reasons.json').read_text())


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['name'])
def test_homa_reason_contract(case):
    facts = case['facts']
    admitted, reasons = homa_election(
        facts['tithi'], facts['vaaram'], facts['nakshatra'], facts['solarNakshatra'])
    assert {'admitted': admitted, 'reasons': reasons} == case['expected']

"""Reproduce a printed primary-source example, not the provisional engine.

All expected constants and results come from the independently inspected scan.
Only two table rows are transcribed; this is not a complete lunar algorithm.
"""
import json
from fractions import Fraction
from pathlib import Path

EXAMPLE = json.loads(
    (Path(__file__).parent / 'fixtures/vakya_1962_worked_example.json').read_text())
FULL_CIRCLE = 360 * 3600


def _arcseconds(angle):
    signs, degrees, minutes, seconds = angle
    return ((signs * 30 + degrees) * 60 + minutes) * 60 + seconds


def test_primary_edition_lunar_example_and_local_sunrise_reduction():
    remainder = EXAMPLE['kali_day'] - EXAMPLE['sodhya_days']
    quotients = []
    for divisor in EXAMPLE['divisors_days']:
        quotient, remainder = divmod(remainder, divisor)
        quotients.append(quotient)
    assert quotients == EXAMPLE['expected_quotients']
    assert remainder == EXAMPLE['expected_remainder']
    dhruva = (_arcseconds(EXAMPLE['base_angle']) + sum(
        q * _arcseconds(angle)
        for q, angle in zip(quotients, EXAMPLE['quotient_angles'], strict=True)
    )) % FULL_CIRCLE
    assert dhruva == _arcseconds(EXAMPLE['expected_dhruva'])
    row = _arcseconds(EXAMPLE['mnemonic_rows'][str(remainder)])
    previous_row = _arcseconds(EXAMPLE['mnemonic_rows'][str(remainder - 1)])
    uncorrected = (dhruva + row) % FULL_CIRCLE
    assert uncorrected == _arcseconds(EXAMPLE['expected_uncorrected'])
    motion = (row - previous_row) % FULL_CIRCLE
    assert motion == _arcseconds(EXAMPLE['expected_daily_motion'])
    vinadis = quotients[2] * 32 - quotients[1] * 8
    assert vinadis == EXAMPLE['expected_correction_vinadis']
    correction = Fraction(
        motion - _arcseconds(EXAMPLE['reference_daily_motion']), 3600) * vinadis
    corrected = (uncorrected + round(correction)) % FULL_CIRCLE
    assert corrected == _arcseconds(EXAMPLE['expected_corrected'])
    local = EXAMPLE['local_example']
    local_correction = Fraction(motion, 3600) * Fraction(local['correction_vinadis'])
    assert corrected + round(local_correction) == _arcseconds(local['expected_longitude'])

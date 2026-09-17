"""Prove issue-count enforcement independently of the coverage gate."""

import pytest

from tools.quality_gate_negative_probe import quality_gate_negative_probe


@pytest.mark.parametrize(('values', 'expected'), [
    ((0, 2, 3, 4, 5, 6), 0),
    ((1, 0, 3, 4, 5, 6), 1),
    ((1, 2, 0, 4, 5, 6), 3),
    ((1, 2, 3, 0, 5, 6), 6),
    ((1, 2, 3, 4, 0, 6), 10),
    ((1, 2, 3, 4, 5, 0), -15),
    ((1, 2, 3, 4, 5, 6), 21),
])
def test_negative_control_calculation_branches(values, expected):
    assert quality_gate_negative_probe(*values) == expected

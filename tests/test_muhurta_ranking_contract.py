"""Hand-authored boundary expectations consumed by both runtime test suites."""

import json
from pathlib import Path

from telugu_panchangam.personal.muhurta import assign_tiers, relative_tier, score_tier

CONTRACT = json.loads(
    (Path(__file__).parent / "fixtures" / "muhurta-ranking-contract.json").read_text()
)


def test_absolute_tier_contract():
    for score, expected in CONTRACT["absolute"]:
        assert score_tier(score) == expected


def test_relative_tier_contract():
    for score, ceiling, floor, expected in CONTRACT["relative"]:
        assert relative_tier(score, ceiling, floor) == expected


def test_batch_tier_contract():
    for case in CONTRACT["batches"]:
        slots = [
            dict(score=score, personal_dosha=personal, day_dosha=day)
            for score, personal, day in zip(
                case["scores"], case["personal"], case["day"]
            )
        ]
        assign_tiers(slots)
        assert [slot["tier"] for slot in slots] == case["expected"]

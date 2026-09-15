"""Reproducible engine-pinned corpus for direct-data versus legacy-view parity."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def build_fixture():
    from telugu_panchangam.cities import CITIES
    from telugu_panchangam.generate import ENGINES
    from telugu_panchangam.generators.calendar_data import calendar_feed

    cases = []
    for system, factory in ENGINES.items():
        for city in ("Hyderabad", "New York"):
            location = next(item for item in CITIES if item.name == city)
            engine = factory()
            for start in (
                date(2026, 3, 3),
                date(2026, 3, 8),
                date(2026, 7, 18),
                date(2026, 1, 14),
            ):
                days = [
                    engine.calculate(start + timedelta(days=i), location)
                    for i in range(2)
                ]
                cases.append(calendar_feed(days, system))
    return cases


if __name__ == "__main__":
    (ROOT / "tests/fixtures/calendar-data-contract.json").write_text(
        json.dumps(build_fixture(), ensure_ascii=False, separators=(",", ":")) + "\n"
    )

"""Project existing Python-owned tables into browser data without changing policy."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def build_export() -> dict:
    from telugu_panchangam import special_yogas as yoga
    from telugu_panchangam.gochara.rules import named_conditions
    from telugu_panchangam.panchangam_names import (
        NAKSHATRA_NAMES,
        RASHI_NAMES,
        VAARAM_NAMES,
        YOGA_NAMES,
    )
    from telugu_panchangam.personal import homa, lagna_hora, nitya_yoga

    # The browser's approximate astronomical path has historically used these
    # spellings. Preserve them here; canonicalizing outputs is a separate change.
    browser_yoga_names = {"Preeti": "Priti", "Shoola": "Shula", "Variyan": "Variyana"}
    return {
        "schemaVersion": 1,
        "rashiNames": RASHI_NAMES,
        "nakshatraNames": NAKSHATRA_NAMES,
        "varaNames": VAARAM_NAMES,
        "browserYogaNames": [browser_yoga_names.get(name, name) for name in YOGA_NAMES],
        "canonicalYogaNames": YOGA_NAMES,
        "nitya": {
            "hardAvoid": sorted(nitya_yoga.NITYA_HARD_AVOID),
            "hardPenalty": nitya_yoga.NITYA_HARD_PENALTY,
            "partialMinutes": {
                name: int(value.total_seconds() / 60)
                for name, value in nitya_yoga.NITYA_PARTIAL_DOSHA_WINDOW.items()
            },
            "partialPenalty": nitya_yoga.NITYA_PARTIAL_PENALTY,
            "auspicious": sorted(nitya_yoga.NITYA_AUSPICIOUS),
            "auspiciousBonus": nitya_yoga.NITYA_AUSPICIOUS_BONUS,
        },
        "specialYoga": {
            "sarvartha": {
                key: sorted(value) for key, value in yoga._SARVARTHA_SIDDHI.items()
            },
            "amrita": yoga._AMRITA_SIDDHI,
            "visha": yoga._VISHA_YOGA,
            "dagdha": {key: sorted(value) for key, value in yoga._DAGDHA_YOGA.items()},
            "pushkaraVaras": sorted(yoga._PUSHKARA_VARAS),
            "dviTithis": sorted(yoga._DVIPUSHKARA_TITHIS),
            "dviNakshatras": sorted(yoga._DVIPUSHKARA_NAKSHATRAS),
            "triTithis": sorted(yoga._TRIPUSHKARA_TITHIS),
            "triNakshatras": sorted(yoga._TRIPUSHKARA_NAKSHATRAS),
        },
        "horaLords": lagna_hora._HORA_LORDS,
        "horaWeekdayStarts": [
            lagna_hora._WEEKDAY_TO_LORD_START[name] for name in VAARAM_NAMES
        ],
        "homaLords": homa.HOMAHUTI_GROUP_LORDS,
        "homaBenefics": sorted(homa.HOMAHUTI_BENEFIC_LORDS),
        "shaniConditions": [
            next(iter(named_conditions(RASHI_NAMES[0], {"Shani": sign})), None)
            for sign in RASHI_NAMES
        ],
    }


def rendered() -> str:
    return json.dumps(build_export(), ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = ROOT / "src/data/shared-calendar-tables.generated.json"
    expected = rendered()
    if args.check:
        if not destination.exists() or destination.read_text() != expected:
            print(
                "Shared calendar tables are stale; run tools/export_shared_calendar_tables.py."
            )
            return 1
    else:
        destination.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

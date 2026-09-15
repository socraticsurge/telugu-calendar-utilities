"""MCP result projection; search and scoring stay in the personal layer."""

import json

from telugu_panchangam.personal.activity_rules import (
    ACTIVITY_ALIASES,
    get_activity_rules,
)

_MUHURTA_DISCLAIMER = (
    "Slots intersect good choghadiya blocks with every inauspicious "
    "window removed (Rahu Kalam, Gulika, Yamagandam, Varjyam, "
    "Durmuhurtham). Scoring: tarabalam +/-1 per person, chandrabalam "
    "+/-1 per person, tithi class (preferred +1 / activity-avoided -1 / "
    "Rikta -2; Pushya nakshatra cancels Rikta entirely, "
    "Sarvartha/Amrita Siddhi partially offsets it to -1), vara match +1, "
    "special-yoga bonuses (Sarvartha/Amrita Siddhi +2, Siddha Yoga +1, "
    "Dvipushkara/Tripushkara +1, Visha/Dagdha -2), "
    "Nitya yoga (auspicious +1, Vyatipata/Vaidhriti -2 + samskara skip, "
    "dosha-window -1), Abhijit/Amrita +2, activity bias +1. "
    "Eclipse days are skipped outright. "
    "Each slot carries a tier (Excellent/Good/Fair/Avoid), assigned "
    "relative to the highest/lowest score found across this search "
    '(so "Excellent" means the best of what turned up, not a fixed '
    "absolute bar), and a reason_groups breakdown "
    "(slot_quality, day_quality, group_fit, "
    "activity_match, notes) for transparent reasoning. "
    "personal_dosha (ashtama_chandra/chandra_avoid/chandra_remedial/null) "
    "flags an unrectified personal Moon caution, and day_dosha "
    "(rikta_tithi/visha_dagdha_yoga/vyatipata_vaidhriti/null) flags a "
    "day-level dosha: either keeps a slot capped below Excellent, and "
    "slots are ranked tier-first (Excellent > Good > "
    "Fair > Avoid), then by score, then preferring dosha-free slots. "
    "Tiers are relative to this search, not a universal standard — "
    '"Good"/"Fair" slots with personal_dosha and day_dosha both null are '
    "workable choices, not just runner-ups. When presenting results, "
    "surface personal_dosha/day_dosha and notes regardless of tier, and "
    "for weddings, major samskaras, or any caution the devotee is unsure "
    "about, recommend consulting their purohit."
)


CONSTRAINT_FIELDS = (
    "allowed_maasams",
    "allowed_maasa_solar_pairs",
    "allowed_varas",
    "avoid_vara_paksha",
    "allowed_solar_classes",
    "allowed_nakshatras",
    "avoid_nakshatras",
    "prefer_nakshatras",
    "allowed_tithi_numbers",
    "prefer_tithi_numbers",
    "avoid_tithi_numbers",
    "required_lagna_class",
    "allowed_lagnas",
    "prefer_lagnas",
    "caution_lagna_solar",
    "daytime_only",
    "forenoon_only",
    "allowed_pakshams",
    "allowed_solar_signs",
    "allowed_tithi_names",
    "skip_on_combust",
    "avoid_janma_nakshatra",
    "avoid_vara_tithi_names",
    "avoid_nitya_yogas",
    "require_homa_election",
    "require_single_daylight_tithi",
    "require_single_daylight_nakshatra",
)


def _activity_profile(activity: str) -> dict:
    rules = get_activity_rules(activity)
    result = {
        "alias_of": ACTIVITY_ALIASES.get(activity),
        "source_claim": rules.get("source_claim"),
        "audit_claim": rules.get("audit_claim"),
        "heuristic_claim": rules.get("heuristic_claim"),
        "related_claims": rules.get("related_claims", []),
        "source_scope": rules.get("source_scope"),
        "manual_prerequisites": rules.get("manual_prerequisites", False),
        "automated_constraints": {
            field: rules[field] for field in CONSTRAINT_FIELDS if field in rules
        },
        "manual_checks": rules.get("manual_checks", []),
    }
    if ACTIVITY_ALIASES.get(activity, activity) == "annaprasana":
        result["source_scope"] = {
            "panchangam_profile": "python_and_mcp",
            "exact_election_chart_assessor": "drik_browser_only",
            "event_chart_policy": "election_chart.annaprasana.raman_transcription_policy_v1",
            "general_election_chart_baseline": "open_issue_284",
        }
    return result


def muhurta_response(request, slots, dropped_days) -> str:
    return json.dumps(
        {
            "start_date": request.start_date,
            "days": request.days,
            "activity": request.activity,
            "resolved_activity": ACTIVITY_ALIASES.get(
                request.activity, request.activity
            ),
            "city": request.city,
            "system": request.system,
            "chandra_mode": request.chandra_mode,
            "ayanamsa": request.ayanamsa,
            "slots": slots[:12],
            "dropped_days": dropped_days,
            "activity_profile": _activity_profile(request.activity),
            "disclaimer": _MUHURTA_DISCLAIMER,
        }
    )

"""Structured browser contract for Muhurtam activity checks.

The browser must never infer whether a source-authored manual check belongs in
the chart, information, or practical section from words in the sentence.  This
module owns that presentation decision alongside an explicit inventory of the
deterministic Panchangam fields and exact personal/election-chart rule IDs used
for every browser activity.

``build_activity_check_contract`` joins the explicit metadata below to the
canonical manual-check text in :mod:`activity_rules`.  Its validation is
deliberately strict: adding, removing, or reordering a browser rule requires an
intentional contract update before the generated browser artefact can refresh.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_RULES,
)
from telugu_panchangam.personal.personal_election import (
    PERSONAL_ELECTION_RULES,
)

ACTIVITY_CHECK_CONTRACT_SCHEMA_VERSION = 2
MANUAL_CHECK_CLASS = 'manual-only'
MANUAL_CHECK_DISPLAY_SECTIONS = ('chart', 'information', 'practical')
MANUAL_CHECK_PURPOSES = ('safety_override',)
CANONICAL_VARAS = (
    'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
    'Guruvaram', 'Shukravaram', 'Shanivaram',
)


# These are fields consumed deterministically by the browser's Panchangam
# shortlist.  Provenance, labels, manual-prerequisite caps, personal rules and
# exact election-chart rules are deliberately represented elsewhere.
DETERMINISTIC_PANCHANGAM_FIELDS: tuple[str, ...] = (
    'avoid_karana',
    'prefer_lagna_class',
    'prefer_choghadiya',
    'skip_on_yoga',
    'skip_on_sankramana',
    'prefer_vara',
    'prefer_tithi_class',
    'avoid_tithi_class',
    'required_lagna_class',
    'allowed_maasams',
    'allowed_maasa_solar_pairs',
    'allowed_varas',
    'avoid_vara_paksha',
    'allowed_solar_classes',
    'allowed_nakshatras',
    'avoid_nakshatras',
    'prefer_nakshatras',
    'allowed_tithi_numbers',
    'prefer_tithi_numbers',
    'avoid_tithi_numbers',
    'avoid_janma_nakshatra',
    'avoid_vara_tithi_names',
    'avoid_nitya_yogas',
    'allowed_lagnas',
    'prefer_lagnas',
    'caution_lagna_solar',
    'daytime_only',
    'require_single_daylight_tithi',
    'require_single_daylight_nakshatra',
    'forenoon_only',
    'allowed_pakshams',
    'require_homa_election',
    'allowed_solar_signs',
    'allowed_tithi_names',
    'skip_on_combust',
)


def _activity(
    *,
    panchangam_fields: Sequence[str] = (),
    personal_rule_ids: Sequence[str] = (),
    election_chart_rule_ids: Sequence[str] = (),
    manual_sections: Sequence[Any] = (),
) -> dict[str, tuple]:
    return {
        'deterministic_panchangam_fields': tuple(panchangam_fields),
        'personal_rule_ids': tuple(personal_rule_ids),
        'election_chart_rule_ids': tuple(election_chart_rule_ids),
        'manual_sections': tuple(manual_sections),
    }


def _manual(
    display_section: str,
    *,
    applicable_varas: Sequence[str] = (),
    purpose: str | None = None,
) -> dict[str, Any]:
    """Describe semantic metadata for one unsplit manual source row."""
    specification: dict[str, Any] = {
        'display_section': display_section,
    }
    if applicable_varas:
        specification['applicable_varas'] = tuple(applicable_varas)
    if purpose is not None:
        specification['purpose'] = purpose
    return specification


# A manual-section item is normally one of the three section names.  A tuple of
# ``(section, display text)`` pairs intentionally splits one mixed source check
# into two honest UI rows without altering or losing the canonical source text.
_GRUHAPRAVESHA_OWNER_RITUAL_SPLIT = (
    (
        'chart',
        (
            'The owner\u2019s Janma Rasi, Nakshatra or Lagna may strengthen '
            'the election.'
        ),
    ),
    ('information', 'Complete worship and Bhootabali before entry.'),
)


# All browser activities are listed explicitly.  The field order follows the
# generated activity-rule contract so diffs remain stable and reviewable.
ACTIVITY_CHECK_SPECS: Mapping[str, dict[str, tuple]] = {
    'any': _activity(),
    'wedding': _activity(
        panchangam_fields=(
            'avoid_karana', 'skip_on_yoga', 'skip_on_sankramana',
            'prefer_vara', 'allowed_maasams', 'allowed_maasa_solar_pairs',
            'allowed_varas', 'allowed_nakshatras', 'avoid_nitya_yogas',
            'allowed_lagnas', 'prefer_lagnas', 'allowed_tithi_names',
            'skip_on_combust',
        ),
        election_chart_rule_ids=(
            'wedding.house-7-vacant', 'wedding.kuja-not-8',
            'wedding.shukra-not-6',
        ),
        manual_sections=(
            'information', 'information', 'chart', 'chart', 'practical',
            'information',
        ),
    ),
    'engagement': _activity(
        panchangam_fields=('allowed_nakshatras',),
        manual_sections=('chart', 'information', 'practical'),
    ),
    'naming': _activity(
        panchangam_fields=(
            'prefer_lagna_class', 'prefer_choghadiya', 'skip_on_yoga',
            'skip_on_sankramana', 'prefer_tithi_class',
            'avoid_tithi_class', 'allowed_varas', 'allowed_nakshatras',
            'avoid_tithi_numbers',
        ),
        manual_sections=(
            'information', 'chart', 'chart', 'chart', 'chart',
            'information',
        ),
    ),
    'annaprasana': _activity(
        panchangam_fields=(
            'prefer_choghadiya', 'skip_on_yoga', 'skip_on_sankramana',
            'prefer_tithi_class', 'avoid_tithi_class', 'allowed_varas',
            'allowed_nakshatras', 'avoid_tithi_numbers', 'allowed_lagnas',
        ),
        election_chart_rule_ids=(
            'annaprasana.house-10-vacant', 'annaprasana.budha-not-7',
            'annaprasana.kuja-not-8', 'annaprasana.shukra-not-9',
            'annaprasana.benefic-occupies-lagna',
            'annaprasana.no-natural-malefic-in-lagna',
        ),
        manual_sections=('information', 'chart', 'chart', 'chart'),
    ),
    'karnavedha': _activity(
        panchangam_fields=(
            'skip_on_yoga', 'skip_on_sankramana', 'prefer_tithi_class',
            'avoid_tithi_class', 'allowed_varas', 'avoid_tithi_numbers',
            'allowed_lagnas', 'daytime_only',
            'require_single_daylight_tithi',
            'require_single_daylight_nakshatra',
        ),
        election_chart_rule_ids=('karnavedha.house-8-vacant',),
        manual_sections=('information', 'chart'),
    ),
    'mundana': _activity(
        panchangam_fields=(
            'skip_on_yoga', 'skip_on_sankramana', 'prefer_tithi_class',
            'avoid_tithi_class', 'allowed_varas', 'allowed_nakshatras',
            'prefer_nakshatras', 'allowed_tithi_numbers', 'allowed_lagnas',
            'forenoon_only', 'allowed_pakshams', 'skip_on_combust',
        ),
        manual_sections=('information', 'chart', 'chart', 'chart', 'chart'),
    ),
    'upanayana': _activity(
        panchangam_fields=(
            'skip_on_yoga', 'skip_on_sankramana', 'prefer_tithi_class',
            'avoid_tithi_class', 'allowed_maasams', 'allowed_varas',
            'allowed_nakshatras', 'allowed_lagnas', 'forenoon_only',
            'allowed_solar_signs', 'allowed_tithi_names',
        ),
        manual_sections=(
            'information',
            _manual('chart', applicable_varas=('Budhavaram',)),
            'chart', 'chart', 'chart', 'chart',
            'information',
        ),
    ),
    'vidyarambha': _activity(
        panchangam_fields=(
            'prefer_choghadiya', 'skip_on_yoga', 'skip_on_sankramana',
            'prefer_tithi_class', 'avoid_tithi_class', 'allowed_varas',
            'allowed_nakshatras', 'allowed_lagnas',
        ),
        election_chart_rule_ids=(
            'vidyarambha.house-8-vacant',
            'vidyarambha.budha-shukra-guru-9',
        ),
        manual_sections=('information', 'information', 'chart', 'chart'),
    ),
    'seemantha': _activity(
        panchangam_fields=(
            'allowed_varas', 'allowed_nakshatras', 'allowed_lagnas',
            'allowed_tithi_names',
        ),
        personal_rule_ids=('personal.seemantha.birth-star-exclusions',),
        election_chart_rule_ids=(
            'seemantha.house-8-vacant', 'seemantha.chandra-not-8',
        ),
        manual_sections=(
            'information', 'information', 'chart', 'chart', 'chart',
            'information', 'practical',
        ),
    ),
    'gruhapravesha': _activity(
        panchangam_fields=(
            'prefer_lagna_class', 'allowed_varas', 'allowed_nakshatras',
            'allowed_lagnas', 'allowed_solar_signs', 'allowed_tithi_names',
        ),
        personal_rule_ids=(
            'personal.gruhapravesha.natal-anchor-match',
        ),
        election_chart_rule_ids=('gruhapravesha.house-8-vacant',),
        manual_sections=(
            'information', 'chart', 'chart',
            _GRUHAPRAVESHA_OWNER_RITUAL_SPLIT, 'practical', 'information',
        ),
    ),
    'vehicle': _activity(
        panchangam_fields=(
            'prefer_lagna_class', 'prefer_choghadiya', 'prefer_vara',
            'prefer_tithi_class', 'prefer_nakshatras',
        ),
    ),
    'property': _activity(
        panchangam_fields=(
            'prefer_lagna_class', 'prefer_vara', 'allowed_varas',
            'allowed_nakshatras', 'avoid_tithi_numbers',
        ),
        election_chart_rule_ids=(
            'property.guru-kendra-trikona', 'property.kuja-11',
            'property.kuja-not-lagna',
        ),
        manual_sections=('chart', 'chart', 'chart', 'chart'),
    ),
    'house_purchase': _activity(
        panchangam_fields=(
            'allowed_varas', 'allowed_nakshatras',
            'allowed_tithi_numbers', 'prefer_lagnas',
        ),
        election_chart_rule_ids=('house-purchase.kuja-not-lagna',),
        manual_sections=('information', 'chart', 'chart', 'practical'),
    ),
    'gold': _activity(
        panchangam_fields=(
            'prefer_lagna_class', 'prefer_choghadiya', 'prefer_vara',
            'prefer_tithi_class',
        ),
        election_chart_rule_ids=(
            'gold.surya-well-situated',
            'gold.chandra-well-situated',
            'gold.surya-fully-aspected',
            'gold.chandra-fully-aspected',
        ),
        manual_sections=('chart',),
    ),
    'business_inventory_purchase': _activity(
        panchangam_fields=(
            'prefer_vara', 'allowed_varas', 'prefer_nakshatras',
            'prefer_tithi_numbers',
        ),
        manual_sections=(
            'information',
            _manual('information', applicable_varas=('Shanivaram',)),
            'chart', 'chart', 'practical',
        ),
    ),
    'purchase': _activity(
        panchangam_fields=('prefer_choghadiya', 'prefer_nakshatras'),
        election_chart_rule_ids=(
            'purchase.chandra-lagna', 'purchase.shukra-lagna',
        ),
        manual_sections=('information', 'chart', 'information'),
    ),
    'borrowing_money': _activity(
        panchangam_fields=('avoid_nakshatras', 'avoid_janma_nakshatra'),
        manual_sections=(
            'information', 'chart', 'chart', 'chart', 'practical',
        ),
    ),
    'lending_money': _activity(
        panchangam_fields=(
            'allowed_varas', 'avoid_nakshatras',
            'avoid_janma_nakshatra', 'avoid_vara_tithi_names',
        ),
        manual_sections=(
            'information', 'chart', 'chart', 'chart', 'information',
            'practical',
        ),
    ),
    'bhumi_puja': _activity(
        panchangam_fields=(
            'skip_on_yoga', 'prefer_vara', 'required_lagna_class',
            'allowed_maasams', 'allowed_varas', 'avoid_vara_paksha',
            'allowed_solar_classes', 'allowed_nakshatras',
            'prefer_nakshatras', 'allowed_tithi_numbers',
        ),
        manual_sections=('chart', 'chart', 'information'),
    ),
    'well_digging': _activity(
        panchangam_fields=(
            'allowed_nakshatras', 'allowed_lagnas', 'caution_lagna_solar',
        ),
        manual_sections=('chart', 'chart'),
    ),
    'home_repair': _activity(
        panchangam_fields=('prefer_vara', 'allowed_varas'),
        manual_sections=(
            'information',
            _manual(
                'chart',
                applicable_varas=('Somavaram', 'Shukravaram'),
            ),
            'chart', 'chart', 'practical',
        ),
    ),
    'business': _activity(
        panchangam_fields=('required_lagna_class', 'allowed_nakshatras'),
        manual_sections=('information', 'chart', 'practical'),
    ),
    'job': _activity(
        panchangam_fields=('allowed_varas', 'allowed_nakshatras'),
        election_chart_rule_ids=('job.surya-or-kuja-10-11',),
        manual_sections=('information', 'chart', 'chart', 'practical'),
    ),
    'yajna': _activity(
        panchangam_fields=('require_homa_election',),
        manual_sections=('information', 'practical'),
    ),
    'pilgrimage': _activity(
        panchangam_fields=(
            'avoid_karana', 'prefer_lagna_class', 'prefer_nakshatras',
            'avoid_tithi_numbers', 'skip_on_combust',
        ),
        election_chart_rule_ids=('pilgrimage.guru-lagna-or-9',),
        manual_sections=('chart',),
    ),
    'ceremony': _activity(
        panchangam_fields=(
            'skip_on_sankramana', 'allowed_varas', 'allowed_nakshatras',
            'avoid_tithi_numbers',
        ),
        election_chart_rule_ids=(
            'ceremony.surya-10', 'ceremony.chandra-4',
            'ceremony.guru-lagna',
        ),
        manual_sections=('information', 'chart', 'chart', 'information'),
    ),
    'court': _activity(
        panchangam_fields=(
            'allowed_varas', 'allowed_nakshatras',
            'avoid_tithi_numbers', 'allowed_lagnas',
        ),
        manual_sections=(
            'information', 'information', 'chart', 'chart', 'chart',
            _manual('practical', purpose='safety_override'),
        ),
    ),
    'surgery': _activity(
        panchangam_fields=(
            'avoid_karana', 'allowed_varas', 'allowed_nakshatras',
            'allowed_tithi_names',
        ),
        personal_rule_ids=(
            'personal.surgery.chandra-outside-janma-rashi',
        ),
        election_chart_rule_ids=('surgery.house-8-vacant',),
        manual_sections=(
            _manual('practical', purpose='safety_override'),
            'chart', 'chart',
        ),
    ),
    'travel': _activity(
        panchangam_fields=(
            'avoid_karana', 'prefer_lagna_class', 'avoid_nakshatras',
            'prefer_nakshatras',
        ),
        personal_rule_ids=(
            'personal.travel.lagna-exclusions',
            'personal.travel.janma-rashi-lagna',
        ),
        election_chart_rule_ids=('travel.kuja-not-8',),
        manual_sections=('chart', 'chart'),
    ),
}


def _rule_ids(rules: Sequence[Any]) -> tuple[str, ...]:
    result = []
    for rule in rules:
        result.append(rule['id'] if isinstance(rule, dict) else rule[0])
    return tuple(result)


def _display_rows(
    activity: str,
    source_index: int,
    source_text: str,
    specification: Any,
) -> list[dict[str, Any]]:
    if isinstance(specification, str):
        presentations = ({
            'display_section': specification,
            'text': source_text,
        },)
    elif isinstance(specification, Mapping):
        presentations = ({**specification, 'text': source_text},)
    else:
        presentations = tuple({
            'display_section': section,
            'text': text,
        } for section, text in specification)

    rows = []
    for part_index, presentation in enumerate(presentations):
        suffix = '' if len(presentations) == 1 else chr(ord('a') + part_index)
        row = {
            'id': f'{activity}.manual-{source_index + 1}{suffix}',
            'source_index': source_index,
            'source_text': source_text,
            'text': presentation['text'],
            'class': MANUAL_CHECK_CLASS,
            'display_section': presentation['display_section'],
        }
        if presentation.get('applicable_varas'):
            row['applicable_varas'] = list(presentation['applicable_varas'])
        if presentation.get('purpose'):
            row['purpose'] = presentation['purpose']
        rows.append(row)
    return rows


def _validate_specs() -> None:
    if tuple(ACTIVITY_CHECK_SPECS) != BROWSER_ACTIVITIES:
        raise ValueError(
            'Activity-check specs must match the ordered browser catalogue')

    allowed_fields = set(DETERMINISTIC_PANCHANGAM_FIELDS)
    allowed_sections = set(MANUAL_CHECK_DISPLAY_SECTIONS)
    for activity, specification in ACTIVITY_CHECK_SPECS.items():
        source_rule = ACTIVITY_RULES[activity]
        fields = specification['deterministic_panchangam_fields']
        expected_fields = tuple(
            field for field in DETERMINISTIC_PANCHANGAM_FIELDS
            if field in source_rule
        )
        if fields != expected_fields:
            raise ValueError(
                f'{activity}: deterministic Panchangam field inventory is '
                'stale')
        unknown_fields = set(fields) - allowed_fields
        if unknown_fields:
            raise ValueError(
                f'{activity}: unknown deterministic fields {unknown_fields!r}')
        missing_fields = [field for field in fields if field not in source_rule]
        if missing_fields:
            raise ValueError(
                f'{activity}: deterministic fields absent from source rule '
                f'{missing_fields!r}')

        personal_ids = _rule_ids(PERSONAL_ELECTION_RULES.get(activity, ()))
        if specification['personal_rule_ids'] != personal_ids:
            raise ValueError(f'{activity}: personal rule IDs are stale')
        election_ids = _rule_ids(ELECTION_CHART_RULES.get(activity, ()))
        if specification['election_chart_rule_ids'] != election_ids:
            raise ValueError(f'{activity}: election-chart rule IDs are stale')

        source_checks = tuple(source_rule.get('manual_checks', ()))
        manual_specs = specification['manual_sections']
        if len(manual_specs) != len(source_checks):
            raise ValueError(
                f'{activity}: expected {len(source_checks)} manual '
                f'classifications, found {len(manual_specs)}')
        for manual_spec in manual_specs:
            if isinstance(manual_spec, str):
                sections = (manual_spec,)
                applicable_varas = ()
                purpose = None
            elif isinstance(manual_spec, Mapping):
                unknown_keys = set(manual_spec) - {
                    'display_section', 'applicable_varas', 'purpose'}
                if unknown_keys:
                    raise ValueError(
                        f'{activity}: unknown manual metadata '
                        f'{unknown_keys!r}')
                sections = (manual_spec.get('display_section'),)
                applicable_varas = tuple(
                    manual_spec.get('applicable_varas', ()))
                purpose = manual_spec.get('purpose')
            else:
                sections = tuple(item[0] for item in manual_spec)
                applicable_varas = ()
                purpose = None
            if not sections or set(sections) - allowed_sections:
                raise ValueError(
                    f'{activity}: invalid manual display sections {sections!r}')
            unknown_varas = set(applicable_varas) - set(CANONICAL_VARAS)
            if unknown_varas:
                raise ValueError(
                    f'{activity}: unknown applicable Varas {unknown_varas!r}')
            if purpose is not None and purpose not in MANUAL_CHECK_PURPOSES:
                raise ValueError(
                    f'{activity}: unknown manual purpose {purpose!r}')


def build_activity_check_contract() -> dict[str, Any]:
    """Return the JSON-ready, validated browser check contract."""
    _validate_specs()
    activities = {}
    for activity, specification in ACTIVITY_CHECK_SPECS.items():
        rows = []
        source_checks = ACTIVITY_RULES[activity].get('manual_checks', ())
        for index, (text, manual_spec) in enumerate(zip(
                source_checks, specification['manual_sections'], strict=True)):
            rows.extend(_display_rows(activity, index, text, manual_spec))
        activities[activity] = {
            'deterministic_panchangam_fields': list(
                specification['deterministic_panchangam_fields']),
            'personal_rule_ids': list(specification['personal_rule_ids']),
            'election_chart_rule_ids': list(
                specification['election_chart_rule_ids']),
            'manual_checks': rows,
        }
    return {
        'schema_version': ACTIVITY_CHECK_CONTRACT_SCHEMA_VERSION,
        'manual_check_class': MANUAL_CHECK_CLASS,
        'display_sections': list(MANUAL_CHECK_DISPLAY_SECTIONS),
        'purposes': list(MANUAL_CHECK_PURPOSES),
        'activities': activities,
    }

"""Structured, source-backed rules for exact Muhurtam election charts.

This module deliberately contains only predicates whose source wording can be
implemented without choosing an aspect model, strength scale, dignity scheme,
or lineage-specific benefic/malefic classification.  Qualitative requirements
remain in ``ACTIVITY_RULES[*]['manual_checks']``.

House occupancy uses all nine projected grahas, including Rahu and Ketu, and
the DashaFlow contract's whole-sign houses.  A rule is evaluated at every
sampled chart state in an offered window by
:mod:`telugu_panchangam.personal.election_chart`.
"""

from __future__ import annotations

ELECTION_CHART_RULE_SCHEMA_VERSION = 1
ELECTION_CHART_HOUSE_SYSTEM = 'whole_sign'
ELECTION_CHART_NODE_CONVENTION = 'mean'
ELECTION_CHART_PLANETS = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)

ELECTION_CHART_SOURCE_LOCATORS = {
    'muhurta.wedding': (
        "Chapter IX, 'Electing a time for marriage,' printed pp. 41-42 "
        '(PDF pp. 45-46)'),
    'muhurta.annaprasana': (
        "Chapter VIII, 'First feeding on rice (Annaprasana),' printed "
        'pp. 21-22 (PDF pp. 25-26)'),
    'muhurta.seemantha': (
        "Chapter VII, 'Seemantha,' printed pp. 20-21 (PDF pp. 24-25)"),
    'muhurta.gruhapravesha': (
        "Chapter XII, 'Entering a new house,' printed pp. 52-54 "
        '(PDF pp. 56-58)'),
    'muhurta.land_purchase.building': (
        "Chapter XII, 'Buying Lands for Buildings,' printed p. 53 "
        '(PDF p. 57)'),
    'muhurta.house_purchase.completed': (
        "Chapter XII, 'Buying Houses,' printed p. 53 (PDF p. 57)"),
    'muhurta.purchase.general': (
        'Nakshatra-prakarana, purchase Muhurta verse 16, printed '
        'pp. 33-34, and marketplace verse 17, printed pp. 34-35'),
    'muhurta.service_entry': (
        "Nakshatra-prakarana, 'Entering the service of a master,' verse 26, "
        'printed p. 38'),
    'muhurta.shantika_paushtika': (
        "Nakshatra-prakarana, 'Shantika and Paushtika Muhurta,' verse 34, "
        'printed pp. 42-43'),
    'muhurta.pilgrimage': (
        "Chapter XIV, 'Journeys' and 'Pilgrimage,' printed pp. 60-62 "
        '(PDF pp. 64-66)'),
    'muhurta.travel': (
        "Chapter XIV, 'Journeys' and 'Long-distance Journeys,' printed "
        'pp. 60-61 (PDF pp. 64-65)'),
    'muhurta.surgery': (
        "Chapter XV, 'Surgical Operations,' printed pp. 64-65 "
        '(PDF pp. 68-69)'),
}


def _rule(
    rule_id: str,
    label: str,
    kind: str,
    effect: str,
    source_claim: str,
    **facts,
) -> dict:
    return {
        'id': rule_id,
        'label': label,
        'kind': kind,
        'effect': effect,
        'source_claim': source_claim,
        'source_locator': ELECTION_CHART_SOURCE_LOCATORS[source_claim],
        **facts,
    }


ELECTION_CHART_RULES: dict[str, tuple[dict, ...]] = {
    'wedding': (
        _rule('wedding.house-7-vacant', '7th house is vacant',
              'house_empty', 'reject', 'muhurta.wedding', house=7),
        _rule('wedding.kuja-not-8', 'Mangala (Kuja) is outside the 8th house',
              'planet_not_house', 'reject', 'muhurta.wedding', planet='Kuja', house=8),
        _rule('wedding.shukra-not-6', 'Shukra is outside the 6th house',
              'planet_not_house', 'reject', 'muhurta.wedding', planet='Shukra', house=6),
    ),
    'annaprasana': (
        _rule('annaprasana.house-10-vacant', '10th house is vacant',
              'house_empty', 'reject', 'muhurta.annaprasana', house=10),
        _rule('annaprasana.budha-not-7', 'Budha is outside the 7th house',
              'planet_not_house', 'reject', 'muhurta.annaprasana', planet='Budha', house=7),
        _rule('annaprasana.kuja-not-8', 'Mangala (Kuja) is outside the 8th house',
              'planet_not_house', 'reject', 'muhurta.annaprasana', planet='Kuja', house=8),
        _rule('annaprasana.shukra-not-9', 'Shukra is outside the 9th house',
              'planet_not_house', 'reject', 'muhurta.annaprasana', planet='Shukra', house=9),
    ),
    'seemantha': (
        _rule('seemantha.house-8-vacant', '8th house is vacant',
              'house_empty', 'reject', 'muhurta.seemantha', house=8),
        _rule('seemantha.chandra-not-8', 'Chandra is outside the 8th house',
              'planet_not_house', 'reject', 'muhurta.seemantha', planet='Chandra', house=8),
    ),
    'gruhapravesha': (
        _rule('gruhapravesha.house-8-vacant', '8th house is vacant',
              'house_empty', 'reject', 'muhurta.gruhapravesha', house=8),
    ),
    'property': (
        _rule('property.guru-kendra-trikona', 'Guru occupies a Kendra or Trikona',
              'planet_in_houses', 'prefer', 'muhurta.land_purchase.building',
              planet='Guru', houses=[1, 4, 5, 7, 9, 10]),
        _rule('property.kuja-11', 'Mangala (Kuja) occupies the 11th house',
              'planet_in_houses', 'prefer', 'muhurta.land_purchase.building',
              planet='Kuja', houses=[11]),
        _rule('property.kuja-not-lagna', 'Mangala (Kuja) is outside Lagna',
              'planet_not_house', 'reject', 'muhurta.land_purchase.building', planet='Kuja', house=1),
    ),
    'house_purchase': (
        _rule('house-purchase.kuja-not-lagna', 'Mangala (Kuja) is outside Lagna',
              'planet_not_house', 'reject', 'muhurta.house_purchase.completed', planet='Kuja', house=1),
    ),
    'purchase': (
        _rule('purchase.chandra-lagna', 'Chandra occupies Lagna',
              'planet_in_houses', 'prefer', 'muhurta.purchase.general',
              planet='Chandra', houses=[1]),
        _rule('purchase.shukra-lagna', 'Shukra occupies Lagna',
              'planet_in_houses', 'prefer', 'muhurta.purchase.general',
              planet='Shukra', houses=[1]),
    ),
    'job': (
        _rule('job.surya-or-kuja-10-11', 'Surya or Mangala (Kuja) occupies the 10th or 11th house',
              'any_planet_in_houses', 'prefer', 'muhurta.service_entry',
              planets=['Surya', 'Kuja'], houses=[10, 11]),
    ),
    'ceremony': (
        _rule('ceremony.surya-10', 'Surya occupies the 10th house',
              'planet_in_houses', 'prefer', 'muhurta.shantika_paushtika',
              planet='Surya', houses=[10]),
        _rule('ceremony.chandra-4', 'Chandra occupies the 4th house',
              'planet_in_houses', 'prefer', 'muhurta.shantika_paushtika',
              planet='Chandra', houses=[4]),
        _rule('ceremony.guru-lagna', 'Guru occupies Lagna',
              'planet_in_houses', 'prefer', 'muhurta.shantika_paushtika',
              planet='Guru', houses=[1]),
    ),
    'pilgrimage': (
        _rule('pilgrimage.guru-lagna-or-9', 'Guru occupies Lagna or the 9th house',
              'planet_in_houses', 'prefer', 'muhurta.pilgrimage',
              planet='Guru', houses=[1, 9]),
    ),
    'travel': (
        _rule('travel.kuja-not-8', 'Mangala (Kuja) is outside the 8th house',
              'planet_not_house', 'reject', 'muhurta.travel', planet='Kuja', house=8),
    ),
    'surgery': (
        _rule('surgery.house-8-vacant', '8th house is vacant',
              'house_empty', 'reject', 'muhurta.surgery', house=8),
    ),
}


# Clause-level remainder shown after deterministic rules have been evaluated.
# These sentences intentionally exclude the clauses represented above so the
# UI never asks a practitioner to re-check a condition it just computed.
ELECTION_CHART_MANUAL_REMAINDERS: dict[str, tuple[str, ...]] = {
    'wedding': (
        'Assess malefic occupancy or hemming around Lagna and any Chandra-Graha association.',
        'Review the optional fortification combinations and both partners’ compatibility, Tarabala, Chandrabala and Panchaka.',
    ),
    'annaprasana': (
        'Assess whether Budha, Guru or Shukra strengthens Lagna and whether a malefic occupies Lagna.',
    ),
    'seemantha': (
        'If relying on Pournami, assess the source’s qualitative Chandra-dignity condition.',
    ),
    'gruhapravesha': (
        'Assess Guru, Shukra and Chandra strength, benefic/malefic placement, rising-Rasi ownership and the Navamsa exception.',
    ),
    'property': (
        'Assess the weekday lord in Lagna, harmony between Lagna and 7th lords, and whether the 11th lord occupies the 12th.',
    ),
    'house_purchase': (
        'Assess whether a malefic occupies the 7th house.',
    ),
    'purchase': (
        'Keep malefics outside the 8th and 12th houses, and assess whether benefics occupy the 2nd, 10th or 11th.',
    ),
    'job': (
        'Assess whether a benefic strengthens Lagna and complete the employer/employee compatibility checks.',
    ),
    'ceremony': (
        'Assess combustion, exceptional omens and whether the remedial-urgency exception applies.',
    ),
    'pilgrimage': (),
    'travel': (
        'Assess general Lagna fortification, whether Guru or Shukra is well placed in Lagna, waxing Chandra and malefic occupancy of the 7th house.',
    ),
    'surgery': (
        'Assess the operated-body-part Rasi and house, malefic affliction, Mangala strength and Mangala-Shani aspects.',
    ),
}

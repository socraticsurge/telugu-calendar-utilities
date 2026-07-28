"""Field-group authority disclosure for the daily Panchangam surface.

This module describes evidence; it does not participate in calculation.
"""
from __future__ import annotations


_GROUPS = (
    {
        'id': 'calendar_semantics',
        'fields': ('metadata',),
        'claim_id': 'panchangam.calendar_semantics',
        'state': 'needs_locator',
        'note': 'Calendar labels and rollover conventions need criterion-level textual locators.',
    },
    {
        'id': 'mixed_daily_windows',
        'fields': (
            'auspicious',
            'inauspicious',
            'choghadiya',
            'choghadiya_night',
        ),
        'claim_id': 'panchangam.mixed_daily_windows',
        'state': 'partially_verified',
        'note': 'Varjyam and Durmuhurtham have inspected textual evidence, but this mixed regional bundle is not uniformly scriptural.',
    },
    {
        'id': 'bhadra_subwindows',
        'fields': ('bhadra_mukha', 'bhadra_puchha'),
        'claim_id': 'panchangam.bhadra_mukha_puchha',
        'state': 'verified',
        'note': 'Muhurta Chintamani 44 supplies the Tithi-specific Mukha and Puchha quarters and nominal widths.',
    },
    {
        'id': 'sankramana_avoidance',
        'fields': ('sankramana_avoidance',),
        'claim_id': 'panchangam.sankramana_avoidance',
        'state': 'verified',
        'note': 'Raman explicitly rejects sixteen Ghatis on each side of solar ingress for new work.',
    },
    {
        'id': 'festival_and_day_labels',
        'fields': ('special_days', 'is_special'),
        'claim_id': 'festivals.forward_year_2027_2028',
        'state': 'partially_verified',
        'note': 'The forward fixture has one independently checked cell; the other cells are engine-pinned.',
    },
    {
        'id': 'eclipse_events',
        'fields': ('eclipse',),
        'claim_id': 'panchangam.eclipse_events',
        'state': 'engine_pinned',
        'note': 'Event calculations are tested but lack an independent comparison fixture in the ledger.',
    },
    {
        'id': 'panchaka_rahita',
        'fields': ('panchaka_rahita',),
        'claim_id': 'panchangam.panchaka_rahita',
        'state': 'verified',
        'note': 'Raman gives the four-factor mod-nine computation, remainder names and activity exceptions.',
    },
    {
        'id': 'other_derived_traditional_classifications',
        'fields': (
            'special_yogas', 'ghati_clock', 'in_panchaka_nakshatra',
            'is_khar_maasa', 'khar_maasa_name', 'is_pitru_paksha',
            'simha_stha_guru', 'simha_stha_shukra', 'guru_maudhya',
            'shukra_maudhya', 'anandadi_yoga', 'disha_shoola_direction',
            'nakshatra_mukha',
        ),
        'claim_id': 'panchangam.derived_classifications',
        'state': 'needs_locator',
        'note': 'Each classification needs its own source crosswalk; this group grants no umbrella authority.',
    },
)


def panchangam_provenance(system: str) -> dict:
    """Return the authority status for every non-identity response category."""
    if system == 'drik':
        astronomical = {
            'id': 'astronomical_core',
            'fields': ['pancha_anga', 'sky'],
            'claim_id': 'drik.sidereal_positions',
            'state': 'partially_verified',
            'note': 'Swiss-Ephemeris calculations have representative golden comparisons, not exhaustive external verification.',
        }
    else:
        astronomical = {
            'id': 'astronomical_core',
            'fields': ['pancha_anga', 'sky'],
            'claim_id': 'panchangam.non_drik_engine_outputs',
            'state': 'engine_pinned',
            'note': 'Surya Siddhanta and Vakya outputs are regression-pinned; no external comparison claim is recorded.',
        }

    groups = [astronomical]
    groups.extend({
        'id': group['id'],
        'fields': list(group['fields']),
        'claim_id': group['claim_id'],
        'state': group['state'],
        'note': group['note'],
    } for group in _GROUPS)
    return {
        'schema_version': 1,
        'surface': 'panchangam',
        'calculation_system': system,
        'coverage_groups': groups,
        'warning': (
            'A computed or regression-pinned value is not thereby a '
            'scripturally verified interpretation. Read each group state and '
            'claim scope independently.'
        ),
    }

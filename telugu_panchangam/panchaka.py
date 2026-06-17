"""Panchaka Rahita — mod-9 dosha computation.

Sum {Tithi (1..30 Shukla then Krishna), Vaaram (1..7), Nakshatra (1..27),
Lagna (1..12)} and mod 9.

  0 -> Rahita        (auspicious)
  1 -> Mrityu        (universal samskara avoidance)
  2 -> Agni          (construction / property restriction)
  3 -> Rahita
  4 -> Raja          (joining service / authority)
  5 -> Rahita
  6 -> Chora         (travel / journey)
  7 -> Rahita
  8 -> Roga          (medical procedure / surgery)

Day-level uses lagna at sunrise. Slot-level recomputes lagna at the
slot's start moment.
"""
from telugu_panchangam.models.panchangam_day import PanchakaInfo
from telugu_panchangam.engines.base import TITHI_NAMES, NAKSHATRA_NAMES, VAARAM_NAMES, RASHI_NAMES


_PANCHAKA_INFO: dict[int, tuple[str, bool, list[str]]] = {
    0: ('Rahita', True, []),
    1: ('Mrityu', False, [
        'ceremony', 'wedding', 'upanayana', 'gruhapravesha', 'engagement',
        'naming', 'annaprasana', 'karnavedha', 'mundana', 'vidyarambha',
        'travel', 'beginning', 'construction', 'purchase',
    ]),
    2: ('Agni', False, ['construction', 'construction_foundation',
                        'construction_roof', 'gruhapravesha',
                        'purchase_property']),
    3: ('Rahita', True, []),
    4: ('Raja', False, ['joining_service', 'job_start',
                        'dealing_with_authority']),
    5: ('Rahita', True, []),
    6: ('Chora', False, ['travel', 'journey']),
    7: ('Rahita', True, []),
    8: ('Roga', False, ['medical_procedure', 'surgery']),
}


def tithi_to_number(tithi_name: str) -> int:
    """Panchaka tithi numbering: Shukla Pratipat=1 .. Pournami=15,
    Krishna Pratipat=16 .. Amavasya=30.

    Input should be the full name as stored in TITHI_NAMES, e.g.
    'Shukla Saptami', 'Pournami', 'Krishna Trayodashi', 'Amavasya'.
    Aliases 'Shukla Pournami' and 'Krishna Amavasya' are also accepted.
    """
    name = tithi_name.strip()
    # Handle aliases not in the canonical list
    if name == 'Shukla Pournami':
        return 15
    if name == 'Krishna Amavasya':
        return 30
    try:
        return TITHI_NAMES.index(name) + 1
    except ValueError:
        raise ValueError(f'Unrecognised tithi: {tithi_name!r}') from None


def nakshatra_to_number(name: str) -> int:
    """1-indexed nakshatra number: Ashvini=1 .. Revati=27."""
    try:
        return NAKSHATRA_NAMES.index(name) + 1
    except ValueError:
        raise ValueError(f'Unrecognised nakshatra: {name!r}') from None


def vaaram_to_number(name: str) -> int:
    """1-indexed weekday: Adivaram=1 .. Shanivaram=7."""
    try:
        return VAARAM_NAMES.index(name) + 1
    except ValueError:
        raise ValueError(f'Unrecognised vaaram: {name!r}') from None


def lagna_to_number(name: str) -> int:
    """1-indexed rasi: Mesha=1 .. Meena=12. Uses RASHI_NAMES order."""
    try:
        return RASHI_NAMES.index(name) + 1
    except ValueError:
        raise ValueError(f'Unrecognised lagna rasi: {name!r}') from None


def get_panchaka_remainder(
    tithi_num: int, vaaram_num: int, nakshatra_num: int, lagna_num: int,
) -> int:
    """(tithi + vaaram + nakshatra + lagna) mod 9."""
    return (tithi_num + vaaram_num + nakshatra_num + lagna_num) % 9


def evaluate_panchaka(
    tithi_name: str, vaaram_name: str, nakshatra_name: str, lagna_name: str,
) -> PanchakaInfo:
    """Compute PanchakaInfo for the given panchangam elements.

    All names should use the canonical strings from the engine tables
    (TITHI_NAMES, VAARAM_NAMES, NAKSHATRA_NAMES, RASHI_NAMES).
    """
    rem = get_panchaka_remainder(
        tithi_to_number(tithi_name),
        vaaram_to_number(vaaram_name),
        nakshatra_to_number(nakshatra_name),
        lagna_to_number(lagna_name),
    )
    panchaka_name, auspicious, avoid_for = _PANCHAKA_INFO[rem]
    return PanchakaInfo(remainder=rem, name=panchaka_name, auspicious=auspicious,
                        avoid_for=list(avoid_for))

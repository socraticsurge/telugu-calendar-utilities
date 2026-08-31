import swisseph as swe

from telugu_panchangam.engines.utils import datetime_to_jd, get_sunrise, jd_to_utc
from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.panchangam_names import RASHI_NAMES

_HORA_LORDS = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']

_WEEKDAY_TO_LORD_START = {
    'Adivaram': 0,      # Sun
    'Somavaram': 3,     # Moon
    'Mangalavaram': 6,  # Mars
    'Budhavaram': 2,    # Mercury
    'Guruvaram': 5,     # Jupiter
    'Shukravaram': 1,   # Venus
    'Shanivaram': 4,    # Saturn
}


def _first_sunrise_after(day: PanchangamDay) -> float:
    """Return the first sunrise after this Panchangam day's sunset.

    Seeding the Swiss Ephemeris search exactly one Julian day after sunrise can
    fall a few seconds beyond the immediately following sunrise.  In that case
    ``get_sunrise`` correctly finds the *second* following sunrise.  Sunset is
    an unambiguous instant inside the requested sunrise cycle, so searching
    from there preserves the documented first-following-sunrise boundary.
    """
    geopos = [day.location.lon, day.location.lat, 0.0]
    return get_sunrise(datetime_to_jd(day.sunset), geopos)

def get_horas(day: PanchangamDay) -> list[Window]:
    """Calculate the 24 planetary hours (horas) for the day.
    12 daytime horas from sunrise to sunset.
    12 nighttime horas from sunset to next sunrise.
    Sequence starts with the weekday lord.
    """
    horas = []

    # Reuse the first-following-sunrise boundary protected by #430/#437.
    jd_next_sunrise = _first_sunrise_after(day)
    next_sunrise = jd_to_utc(jd_next_sunrise)

    day_duration = day.sunset - day.sunrise
    night_duration = next_sunrise - day.sunset

    day_hora_len = day_duration / 12
    night_hora_len = night_duration / 12

    lord_idx = _WEEKDAY_TO_LORD_START[day.vaaram]

    # 12 Daytime Horas
    start_time = day.sunrise
    for i in range(12):
        end_time = day.sunrise + (i + 1) * day_hora_len
        lord_name = _HORA_LORDS[(lord_idx + i) % 7]
        horas.append(Window(name=f'{lord_name} Hora', start=start_time, end=end_time))
        start_time = end_time

    # 12 Nighttime Horas
    start_time = day.sunset
    for i in range(12):
        end_time = day.sunset + (i + 1) * night_hora_len
        lord_name = _HORA_LORDS[(lord_idx + 12 + i) % 7]
        horas.append(Window(name=f'{lord_name} Hora', start=start_time, end=end_time))
        start_time = end_time

    return horas

def get_lagna_transitions(day: PanchangamDay) -> list[Window]:
    """Calculate Ascendant (Lagna) sign boundaries from sunrise to next sunrise.
    Returns a list of Windows, each representing the duration of a Lagna.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # Calculate the first following sunrise from an instant safely inside the
    # requested cycle.  See #430 for the former two-cycle regression.
    jd_start = datetime_to_jd(day.sunrise)
    jd_end = _first_sunrise_after(day)

    transitions = []
    current_jd = jd_start
    step_jd = 5.0 / (24 * 60) # 5 minutes in days

    def get_ascendant_sign(jd):
        # Calculate house cusps (0 = Placidus). Parameter needs to be bytes, so b'P'
        _cusps, ascmc = swe.houses(jd, day.location.lat, day.location.lon, b'P')
        ascendant_deg = ascmc[0] # Ascendant is the first element

        # Apply Ayanamsa to get sidereal degree
        ayanamsa = swe.get_ayanamsa_ut(jd)
        sidereal_deg = (ascendant_deg - ayanamsa) % 360

        return int(sidereal_deg / 30.0) % 12

    def find_transition_bisection(jd_low, jd_high, sign_low):
        # Find exact transition time using bisection.
        # We need accuracy to at least a minute, so epsilon is 0.5 minutes.
        epsilon = 0.5 / (24 * 60)
        while (jd_high - jd_low) > epsilon:
            jd_mid = (jd_low + jd_high) / 2
            sign_mid = get_ascendant_sign(jd_mid)
            if sign_mid == sign_low:
                jd_low = jd_mid
            else:
                jd_high = jd_mid
        return (jd_low + jd_high) / 2

    start_sign_idx = get_ascendant_sign(current_jd)
    window_start = jd_to_utc(current_jd)
    current_sign_idx = start_sign_idx

    while current_jd < jd_end:
        next_jd = min(current_jd + step_jd, jd_end)

        sign_idx = get_ascendant_sign(next_jd)
        if sign_idx != current_sign_idx:
            exact_jd = find_transition_bisection(current_jd, next_jd, current_sign_idx)
            window_end = jd_to_utc(exact_jd)
            transitions.append(Window(
                name=f'{RASHI_NAMES[current_sign_idx]} Lagna',
                start=window_start,
                end=window_end
            ))
            window_start = window_end
            current_sign_idx = sign_idx

        current_jd = next_jd

    # Add the last window
    transitions.append(Window(
        name=f'{RASHI_NAMES[current_sign_idx]} Lagna',
        start=window_start,
        end=jd_to_utc(jd_end)
    ))

    return transitions

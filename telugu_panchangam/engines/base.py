from abc import ABC, abstractmethod
from datetime import date
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay

TITHI_NAMES: list[str] = [
    # Shukla Paksha (0-14)
    'Shukla Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya', 'Shukla Chaturthi',
    'Shukla Panchami', 'Shukla Shashthi', 'Shukla Saptami', 'Shukla Ashtami',
    'Shukla Navami', 'Shukla Dashami', 'Shukla Ekadashi', 'Shukla Dwadashi',
    'Shukla Trayodashi', 'Shukla Chaturdashi', 'Pournami',
    # Krishna Paksha (15-29)
    'Krishna Pratipat', 'Krishna Dwitiya', 'Krishna Tritiya', 'Krishna Chaturthi',
    'Krishna Panchami', 'Krishna Shashthi', 'Krishna Saptami', 'Krishna Ashtami',
    'Krishna Navami', 'Krishna Dashami', 'Krishna Ekadashi', 'Krishna Dwadashi',
    'Krishna Trayodashi', 'Krishna Chaturdashi', 'Amavasya',
]

NAKSHATRA_NAMES: list[str] = [
    'Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha',
    'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha',
    'Shravana', 'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati',
]

YOGA_NAMES: list[str] = [
    'Vishkambha', 'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
    'Sukarma', 'Dhriti', 'Shoola', 'Ganda', 'Vriddhi', 'Dhruva',
    'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan',
    'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla',
    'Brahma', 'Indra', 'Vaidhriti',
]

RASHI_NAMES: list[str] = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
    'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
]

MAASAM_NAMES: list[str] = [
    'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha',
    'Shravana', 'Bhadrapada', 'Ashvina', 'Kartika',
    'Margashira', 'Pushya', 'Magha', 'Phalguna',
]

SAMVATSARA_NAMES: list[str] = [
    'Prabhava', 'Vibhava', 'Shukla', 'Pramoduta', 'Prajapati',
    'Angirasa', 'Shrimukha', 'Bhava', 'Yuva', 'Dhata',
    'Ishvara', 'Bahudhanya', 'Pramadi', 'Vikrama', 'Vrisha',
    'Chitrabhanu', 'Subhanu', 'Tarana', 'Parthiva', 'Vyaya',
    'Sarvajit', 'Sarvadharin', 'Virodhi', 'Vikrita', 'Khara',
    'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukhi',
    'Hevilambi', 'Vilambi', 'Vikari', 'Sharvari', 'Plava',
    'Shubhakrit', 'Shobhakrit', 'Krodhi', 'Vishvavasu', 'Parabhava',
    'Plavanga', 'Kilaka', 'Saumya', 'Sadharana', 'Virodhikrit',
    'Paridhavi', 'Pramadicha', 'Ananda', 'Rakshasa', 'Nala',
    'Pingala', 'Kalayukti', 'Siddharthi', 'Raudra', 'Durmati',
    'Dundubhi', 'Rudhirodgari', 'Raktakshi', 'Krodhana', 'Kshaya',
]

RITUVU_NAMES: list[str] = [
    'Vasanta', 'Vasanta',      # Mesha, Vrishabha
    'Grishma', 'Grishma',      # Mithuna, Karka
    'Varsha', 'Varsha',        # Simha, Kanya
    'Sharad', 'Sharad',        # Tula, Vrischika
    'Hemanta', 'Hemanta',      # Dhanu, Makara
    'Shishira', 'Shishira',    # Kumbha, Meena
]

VAARAM_NAMES: list[str] = [
    'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
    'Guruvaram', 'Shukravaram', 'Shanivaram',
]

KARANA_REPEATING: list[str] = [
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garaja', 'Vanija', 'Vishti',
]
KARANA_FIXED: dict[int, str] = {
    0: 'Kinstughna',
    57: 'Shakuni',
    58: 'Chatushpada',
    59: 'Naga',
}


_KALI_EPOCH_JD = 588465.5
_SIDEREAL_YEAR_DAYS = 365.25636


def samvatsara_name(jd: float, maasam: str) -> str:
    """Telugu (southern, Chaitradi) 60-year Samvatsara name at instant `jd`.

    Counts solar years elapsed since the Kali epoch. The ahargana is shifted
    by the current lunar month so the year flips at Chaitra (Ugadi) rather
    than at the mean solar boundary. Offset +12 anchors the cycle so that
    Kali 5128 (2026-27 CE) is Parabhava.
    """
    base = maasam.removeprefix('Adhika ').removeprefix('Nija ')
    maasa_num = MAASAM_NAMES.index(base) + 1
    ahargana = jd - _KALI_EPOCH_JD
    kali_elapsed = int((ahargana + (4 - maasa_num) * 30) / _SIDEREAL_YEAR_DAYS)
    return SAMVATSARA_NAMES[(kali_elapsed + 12) % 60]


def maasam_name(elongation_func, sun_longitude_func, jd_sunrise: float) -> str:
    """Amanta lunar month name at jd_sunrise, with Adhika/Nija prefix.

    The month is named from the sun's sign at its starting new moon. When the
    sun occupies the same sign at both bounding new moons, the month contains
    no sankranti and is Adhika; the following month repeats the name as Nija.
    """
    from telugu_panchangam.engines.utils import next_new_moon, previous_new_moon

    nm_start = previous_new_moon(elongation_func, jd_sunrise)
    sign_start = int(sun_longitude_func(nm_start) / 30.0) % 12
    name = MAASAM_NAMES[(sign_start - 11) % 12]

    nm_end = next_new_moon(elongation_func, nm_start + 1.0)
    if sign_start == int(sun_longitude_func(nm_end) / 30.0) % 12:
        return f'Adhika {name}'

    nm_prev = previous_new_moon(elongation_func, nm_start - 1.0)
    if sign_start == int(sun_longitude_func(nm_prev) / 30.0) % 12:
        return f'Nija {name}'

    return name


# Traditional Ekadashi names by Amanta maasam and paksham. Both Ekadashis of
# an Adhika maasam have their own names (Padmini/Parama) regardless of month.
EKADASHI_NAMES: dict[str, dict[str, str]] = {
    'Chaitra':    {'Shukla': 'Kamada',      'Krishna': 'Varuthini'},
    'Vaishakha':  {'Shukla': 'Mohini',      'Krishna': 'Apara'},
    'Jyeshtha':   {'Shukla': 'Nirjala',     'Krishna': 'Yogini'},
    'Ashadha':    {'Shukla': 'Shayani',     'Krishna': 'Kamika'},
    'Shravana':   {'Shukla': 'Putrada',     'Krishna': 'Aja'},
    'Bhadrapada': {'Shukla': 'Parivartini', 'Krishna': 'Indira'},
    'Ashvina':    {'Shukla': 'Papankusha',  'Krishna': 'Rama'},
    'Kartika':    {'Shukla': 'Prabodhini',  'Krishna': 'Utpanna'},
    'Margashira': {'Shukla': 'Mokshada',    'Krishna': 'Saphala'},
    'Pushya':     {'Shukla': 'Putrada',     'Krishna': 'Shattila'},
    'Magha':      {'Shukla': 'Jaya',        'Krishna': 'Vijaya'},
    'Phalguna':   {'Shukla': 'Amalaki',     'Krishna': 'Papamochani'},
}


def ekadashi_name(maasam: str, paksham: str, solar_sign: str) -> str | None:
    """Traditional name of the Ekadashi falling in `maasam`/`paksham`.

    Vaikunta (Mukkoti) Ekadashi is tied to Dhanurmasa — the Shukla Ekadashi
    while the sun is in Dhanu — not to a fixed lunar month.
    """
    if maasam.startswith('Adhika'):
        return 'Padmini' if paksham == 'Shukla' else 'Parama'
    name = EKADASHI_NAMES.get(maasam.removeprefix('Nija '), {}).get(paksham)
    if name and paksham == 'Shukla' and solar_sign == 'Dhanu':
        return f'{name} (Vaikunta)'
    return name


class PanchangamEngine(ABC):
    @abstractmethod
    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        """Calculate full Panchangam for a single date and location."""
        ...

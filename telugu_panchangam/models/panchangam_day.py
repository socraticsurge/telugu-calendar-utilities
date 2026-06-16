from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Location:
    name: str
    lat: float
    lon: float
    timezone: str


@dataclass
class Span:
    name: str
    start: datetime
    end: datetime


@dataclass
class Window:
    name: str
    start: datetime
    end: datetime


@dataclass
class GhatiClock:
    """Ghati/vighati clock anchored at sunrise.
    1 ghati = 1/60 ahoratri (sunrise→next-sunrise). 60 vighatis = 1 ghati.
    """
    sunrise: datetime
    next_sunrise: datetime
    seconds_per_ghati: float


@dataclass
class GhatiWindow:
    """A window expressed in both civil time and ghatis-from-sunrise."""
    name: str
    start: datetime
    end: datetime
    start_ghati: float
    end_ghati: float


@dataclass
class EclipseInfo:
    kind: str        # 'Solar' | 'Lunar'
    subtype: str     # 'Total' | 'Partial' | 'Annular' | 'Penumbral'
    visible: bool    # visible from this location
    start: datetime
    end: datetime
    sutak_start: datetime | None  # None if not visible (no Sutak observed)
    sutak_end: datetime | None


@dataclass
class SlotFacts:
    """Panchangam facts active at a specific instant — used by the muhurta
    slot finder to score each candidate slot against its actual moment,
    not against the day's sunrise snapshot.

    `vaaram` is the weekday of the panchangam day this instant belongs to
    (which is constant across the day, anchored at sunrise) — it does NOT
    flip at civil midnight.
    """
    nakshatra: str
    tithi: str
    yoga: str           # Nitya yoga
    karana: str
    lunar_sign: str     # Moon's rashi
    vaaram: str
    special_yogas: list[str]


@dataclass
class PanchangamDay:
    # Identity
    date: date
    location: Location
    system: str  # 'drik' | 'surya_siddhanta' | 'vakya'

    # Metadata
    samvatsara: str
    ayanam: str          # 'Uttarayanam' | 'Dakshinayanam'
    rituvu: str
    maasam: str
    paksham: str         # 'Shukla' | 'Krishna'

    # Five elements
    tithi: Span
    vaaram: str
    nakshatra: Span
    yoga: Span
    karana: list[Span]

    # Solar & lunar markers
    sunrise: datetime
    sunset: datetime
    moonrise: datetime
    moonset: datetime
    solar_sign: str
    lunar_sign: str

    # Auspicious windows
    brahma_muhurta: Window
    abhijit_muhurta: Window | None
    amrita_kalam: list[Window]

    # Inauspicious windows
    rahu_kalam: Window
    gulika_kalam: Window
    yamagandam: Window
    varjyam: list[Window]
    durmuhurtham: list[Window]

    # Choghadiya
    choghadiya: list[Window]

    # Special flags
    is_ekadashi: bool
    is_amavasya: bool
    is_pournami: bool
    is_pradosham: bool
    is_shani_pradosham: bool
    is_soma_pradosham: bool
    is_sankranti: bool
    special_notes: list[str] = field(default_factory=list)
    eclipse: EclipseInfo | None = None
    special_yogas: list[str] = field(default_factory=list)
    festivals: list[str] = field(default_factory=list)
    # Rashi the sun enters this day (entry-after-sunset counts as next day),
    # e.g. 'Mithuna' — None on ordinary days.
    sankramanam: str | None = None
    ghati_clock: 'GhatiClock | None' = None
    nakshatra_pada: int | None = None
    vishaghati: list['GhatiWindow'] = field(default_factory=list)
    bhadra_mukha: 'GhatiWindow | None' = None
    bhadra_puchha: 'GhatiWindow | None' = None
    sankramana_avoidance: 'Window | None' = None
    in_panchaka_nakshatra: bool = False
    is_khar_maasa: bool = False
    khar_maasa_name: str | None = None

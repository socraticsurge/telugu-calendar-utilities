from __future__ import annotations
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

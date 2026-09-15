"""Preserved public MCP argument contract, including introspection and defaults."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FindMuhurtaRequest:
    start_date: str
    days: int = 7
    activity: str = "any"
    city: str = "Hyderabad"
    system: str = "drik"
    janma_nakshatras: Optional[list] = None
    janma_rasis: Optional[list] = None
    janma_lagnas: Optional[list] = None
    chandra_mode: str = "stars"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    ayanamsa: str = "lahiri"
    travel_direction: Optional[str] = None
    include_night: bool = False

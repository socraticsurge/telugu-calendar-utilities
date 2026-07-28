"""Bounded request models for the versioned HTTP adapter."""

from datetime import date
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from telugu_panchangam.engines.utils import AYANAMSA_MODES
from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES, RASHI_NAMES
from telugu_panchangam.personal.activity_rules import ACTIVITIES

SystemName = Literal["drik", "surya_siddhanta", "vakya"]
AyanamsaName = Literal["lahiri", "raman", "krishnamurti", "true_chitrapaksha"]
ChandraMode = Literal["stars", "puja_ok", "strict"]
TravelDirection = Literal["North", "South", "East", "West"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LocationRequest(StrictModel):
    city: str = Field(default="Hyderabad", min_length=1, max_length=80)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def complete_coordinates(self):
        supplied = (self.latitude is not None, self.longitude is not None)
        if any(supplied) and not all(supplied):
            raise ValueError("latitude and longitude must be supplied together")
        if all(supplied) and self.timezone is None:
            raise ValueError("timezone is required with explicit coordinates")
        return self

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value

    def location_kwargs(self) -> dict:
        return {
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
        }


class EngineRequest(LocationRequest):
    system: SystemName = "drik"
    ayanamsa: AyanamsaName = "lahiri"


class PanchangamDayRequest(EngineRequest):
    date: date


class PanchangamRangeRequest(EngineRequest):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def bounded_range(self):
        span = (self.end_date - self.start_date).days + 1
        if span < 1:
            raise ValueError("end_date must not precede start_date")
        if span > 31:
            raise ValueError("date range must not exceed 31 inclusive days")
        return self


class RasiPhalaluRequest(LocationRequest):
    date: date
    janma_rasi: str = Field(min_length=1, max_length=80)
    janma_nakshatra: str | None = Field(default=None, min_length=1, max_length=80)
    ayanamsa: AyanamsaName = "lahiri"

    @field_validator("janma_rasi")
    @classmethod
    def known_rasi(cls, value: str) -> str:
        if value not in RASHI_NAMES:
            raise ValueError("janma_rasi is not supported")
        return value

    @field_validator("janma_nakshatra")
    @classmethod
    def known_optional_nakshatra(cls, value: str | None) -> str | None:
        if value is not None and value not in NAKSHATRA_NAMES:
            raise ValueError("janma_nakshatra is not supported")
        return value


class ParticipantContext(StrictModel):
    label: str = Field(pattern=r"^p[1-4]$")
    janma_nakshatra: str = Field(min_length=1, max_length=80)
    janma_rasi: str | None = Field(default=None, min_length=1, max_length=80)
    janma_lagna: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("janma_nakshatra")
    @classmethod
    def known_nakshatra(cls, value: str) -> str:
        if value not in NAKSHATRA_NAMES:
            raise ValueError("janma_nakshatra is not supported")
        return value

    @field_validator("janma_rasi", "janma_lagna")
    @classmethod
    def known_optional_rasi(cls, value: str | None) -> str | None:
        if value is not None and value not in RASHI_NAMES:
            raise ValueError("rasi is not supported")
        return value


class ParticipantRequest(EngineRequest):
    participants: list[ParticipantContext]

    @model_validator(mode="after")
    def unique_labels(self):
        labels = [participant.label for participant in self.participants]
        if len(labels) != len(set(labels)):
            raise ValueError("participant labels must be unique")
        return self


class TarabalamRequest(ParticipantRequest):
    start_date: date
    days: int = Field(default=14, ge=1, le=90)
    chandra_mode: ChandraMode = "stars"
    participants: list[ParticipantContext] = Field(min_length=1, max_length=4)
    # The existing canonical MCP Tarabalam tool is Lahiri-only. Keep the first
    # HTTP contract honest until that upstream boundary is versioned explicitly.
    ayanamsa: Literal["lahiri"] = "lahiri"


class MuhurtamSearchRequest(ParticipantRequest):
    start_date: date
    days: int = Field(default=7, ge=1, le=14)
    activity: str = Field(default="any", min_length=1, max_length=80)
    participants: list[ParticipantContext] = Field(default_factory=list, max_length=4)
    chandra_mode: ChandraMode = "stars"
    travel_direction: TravelDirection | None = None
    include_night: bool = False

    @field_validator("activity")
    @classmethod
    def known_activity(cls, value: str) -> str:
        if value not in ACTIVITIES:
            raise ValueError("activity is not supported")
        return value

    @model_validator(mode="after")
    def travel_direction_only_for_travel(self):
        if self.travel_direction is not None and self.activity != "travel":
            raise ValueError("travel_direction is valid only for travel")
        return self


assert set(AyanamsaName.__args__) == set(AYANAMSA_MODES)

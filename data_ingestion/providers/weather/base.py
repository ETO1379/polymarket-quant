from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from data_ingestion.core.models import WeatherRaw


@dataclass(slots=True)
class ProviderMetadata:
    name: str
    version: str = "0.1"
    capabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WeatherRequest:
    location_id: str
    lat: float
    lon: float
    timezone: str
    variable: str
    start_date: date | None = None
    end_date: date | None = None
    model: str | None = None
    provider_type: str = "forecast"


class WeatherProvider(Protocol):
    name: str

    def get_forecast(self, request: WeatherRequest) -> list[WeatherRaw]:
        ...

    def get_observation(self, request: WeatherRequest) -> list[WeatherRaw]:
        ...

    def get_metadata(self) -> ProviderMetadata:
        ...

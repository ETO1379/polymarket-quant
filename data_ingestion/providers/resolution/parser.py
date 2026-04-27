from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from data_ingestion.core.models import MarketWeatherMapping
from data_ingestion.core.time import utc_now


SOURCE_PATTERNS = [
    (re.compile(r"\bNational Weather Service\b|\bNWS\b", re.I), "National Weather Service", "https://www.weather.gov/", "noaa"),
    (re.compile(r"\bNOAA\b", re.I), "NOAA", "https://www.noaa.gov/", "noaa"),
    (re.compile(r"\bCMA\b|中国气象", re.I), "CMA / 中国气象数据网", None, "cma"),
]

TIMEZONE_PATTERN = re.compile(r"\b(?:America|US|Asia|Europe|UTC)/[A-Za-z_]+|\bUTC\b")
DATE_PATTERN = re.compile(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})", re.I)


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass(slots=True)
class ResolutionParser:
    default_forecast_provider: str = "open_meteo"

    def parse(self, market: Any) -> MarketWeatherMapping:
        now = utc_now()
        market_id = str(_field(market, "market_id") or _field(market, "id") or "")
        event_id = _field(market, "event_id")
        question = str(_field(market, "question", "") or "")
        description = str(_field(market, "description", "") or "")
        rules = str(_field(market, "rules", "") or "")
        text = " ".join(part for part in (question, description, rules) if part)

        source_name, source_url, observation_provider = self._parse_source(text)
        target_variable, unit = self._parse_variable_and_unit(text)
        timezone = self._parse_timezone(text)
        target_date = self._parse_date(text)
        location_name = self._parse_location(text)

        parsed = bool(source_name and target_variable and timezone)
        if not parsed:
            return MarketWeatherMapping(
                market_id=market_id,
                event_id=event_id,
                resolution_rules_raw_ref=rules or description or question,
                resolution_source_name=None,
                forecast_provider=self.default_forecast_provider,
                forecast_model="GFS",
                observation_provider=observation_provider,
                target_variable=target_variable,
                target_date=target_date,
                timezone=timezone,
                unit=unit,
                parsing_status="manual_review",
                parsing_reason="resolution source, variable, or timezone is unclear",
                created_at=now,
                updated_at=now,
            )

        return MarketWeatherMapping(
            market_id=market_id,
            event_id=event_id,
            location_id=self._location_id(location_name),
            location_name=location_name,
            lat=self._known_lat_lon(location_name)[0],
            lon=self._known_lat_lon(location_name)[1],
            station_id=self._station_id(location_name),
            resolution_rules_raw_ref=rules or description or question,
            resolution_source_name=source_name,
            resolution_source_url=source_url,
            forecast_provider=self.default_forecast_provider,
            forecast_model="GFS",
            observation_provider=observation_provider,
            target_variable=target_variable,
            target_date=target_date,
            target_time_window="local day",
            timezone=timezone,
            unit=unit,
            parsing_status="parsed",
            parsing_reason=None,
            created_at=now,
            updated_at=now,
        )

    def _parse_source(self, text: str) -> tuple[str | None, str | None, str | None]:
        for pattern, name, url, observation_provider in SOURCE_PATTERNS:
            if pattern.search(text):
                return name, url, observation_provider
        return None, None, None

    def _parse_variable_and_unit(self, text: str) -> tuple[str | None, str | None]:
        lowered = text.lower()
        unit = "F" if re.search(r"\b\d+\s*f\b|fahrenheit", lowered) else None
        if "highest" in lowered or "maximum" in lowered or "max" in lowered or "over" in lowered or "record" in lowered:
            if "temp" in lowered or re.search(r"\b\d+\s*f\b", lowered):
                return "temperature_2m_max", unit or "F"
        if "lowest" in lowered or "minimum" in lowered or "min" in lowered:
            return "temperature_2m_min", unit
        if "rain" in lowered or "precipitation" in lowered:
            return "precipitation_sum", "inch" if "inch" in lowered else None
        if "snow" in lowered:
            return "snowfall_sum", "inch" if "inch" in lowered else None
        if "wind" in lowered or "gust" in lowered:
            return "wind_speed_10m_max", "mph" if "mph" in lowered else None
        return None, unit

    def _parse_timezone(self, text: str) -> str | None:
        match = TIMEZONE_PATTERN.search(text)
        if match:
            return "America/New_York" if match.group(0) == "US/Eastern" else match.group(0)
        return None

    def _parse_date(self, text: str) -> date | None:
        match = DATE_PATTERN.search(text)
        if not match:
            return None
        value = match.group(1).replace(".", "")
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
            try:
                from datetime import datetime

                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_location(self, text: str) -> str | None:
        if re.search(r"central park|nyc|new york", text, re.I):
            return "NYC Central Park"
        if re.search(r"chicago", text, re.I):
            return "Chicago"
        if re.search(r"beijing|北京", text, re.I):
            return "Beijing"
        return None

    def _location_id(self, location_name: str | None) -> str | None:
        if not location_name:
            return None
        return re.sub(r"[^a-z0-9]+", "_", location_name.lower()).strip("_")

    def _known_lat_lon(self, location_name: str | None) -> tuple[float | None, float | None]:
        known = {
            "NYC Central Park": (40.7812, -73.9665),
            "Chicago": (41.8781, -87.6298),
            "Beijing": (39.9042, 116.4074),
        }
        return known.get(location_name, (None, None))

    def _station_id(self, location_name: str | None) -> str | None:
        if location_name == "NYC Central Park":
            return "USW00094728"
        return None

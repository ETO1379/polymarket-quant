from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from data_ingestion.core.models import MarketWeatherMapping, WeatherRaw
from data_ingestion.core.time import parse_datetime, utc_now
from data_ingestion.providers.polymarket.http import HttpJsonClient
from data_ingestion.providers.weather.base import ProviderMetadata, WeatherRequest


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass(slots=True)
class WeatherRequestBuilder:
    def build_forecast_request(self, mapping: MarketWeatherMapping, *, allow_live_trading: bool = False) -> WeatherRequest:
        status = _field(mapping, "parsing_status")
        if allow_live_trading and status != "parsed":
            raise ValueError("only parsed MarketWeatherMapping can build live trading weather request")
        lat = _field(mapping, "lat")
        lon = _field(mapping, "lon")
        if lat is None or lon is None:
            raise ValueError("lat/lon are required for weather request")
        variable = _field(mapping, "target_variable") or "temperature_2m"
        return WeatherRequest(
            location_id=_field(mapping, "location_id") or _field(mapping, "market_id"),
            lat=float(lat),
            lon=float(lon),
            timezone=_field(mapping, "timezone") or "UTC",
            variable=variable,
            start_date=_field(mapping, "target_date"),
            end_date=_field(mapping, "target_date"),
            model=_field(mapping, "forecast_model") or "GFS",
            provider_type="forecast",
        )

    def build_request(self, mapping: MarketWeatherMapping, *, allow_live_trading: bool = False) -> WeatherRequest:
        return self.build_forecast_request(mapping, allow_live_trading=allow_live_trading)

    def build(self, mapping: MarketWeatherMapping, *, allow_live_trading: bool = False) -> WeatherRequest:
        return self.build_forecast_request(mapping, allow_live_trading=allow_live_trading)


class OpenMeteoProvider:
    name = "open_meteo"

    def __init__(self, client: HttpJsonClient | None = None) -> None:
        self.client = client or HttpJsonClient("https://api.open-meteo.com/v1", timeout_seconds=10, retry_times=3)

    def get_forecast(self, request: WeatherRequest) -> list[WeatherRaw]:
        is_daily = _is_daily_variable(request.variable)
        params = {
                "latitude": request.lat,
                "longitude": request.lon,
                "timezone": request.timezone,
                "daily" if is_daily else "hourly": request.variable,
        }
        if request.start_date:
            params["start_date"] = request.start_date.isoformat()
        if request.end_date:
            params["end_date"] = request.end_date.isoformat()
        payload = self.client.get_json("/forecast", params=_without_none(params))
        return self._parse_series(payload, request, provider_type="forecast")

    def get_observation(self, request: WeatherRequest) -> list[WeatherRaw]:
        is_daily = _is_daily_variable(request.variable)
        params = {
                "latitude": request.lat,
                "longitude": request.lon,
                "timezone": request.timezone,
                "daily" if is_daily else "hourly": request.variable,
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None,
        }
        payload = self.client.get_json("/archive", params=_without_none(params))
        return self._parse_series(payload, request, provider_type="observation")

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            version="0.1",
            capabilities=["forecast", "historical_weather", "gfs_via_open_meteo", "cma_via_open_meteo"],
        )

    def _parse_series(self, payload: dict[str, Any], request: WeatherRequest, *, provider_type: str) -> list[WeatherRaw]:
        section_name = "daily" if _is_daily_variable(request.variable) else "hourly"
        series = payload.get(section_name, {}) if isinstance(payload, dict) else {}
        times = series.get("time", [])
        values = series.get(request.variable, [])
        units = payload.get(f"{section_name}_units", {}) if isinstance(payload, dict) else {}
        unit = units.get(request.variable, "")
        fetched_at = utc_now()
        rows: list[WeatherRaw] = []
        for time_value, value in zip(times, values, strict=False):
            timestamp = parse_datetime(time_value)
            rows.append(
                WeatherRaw(
                    source=self.name,
                    provider_type=provider_type,
                    model=request.model,
                    run_time=None,
                    forecast_time=timestamp if provider_type == "forecast" else None,
                    observed_time=timestamp if provider_type == "observation" else None,
                    location_id=request.location_id,
                    lat=request.lat,
                    lon=request.lon,
                    timezone=request.timezone,
                    variable=request.variable,
                    value=float(value) if value is not None else None,
                    unit=unit,
                    raw_data_ref=_payload_ref(payload),
                    fetched_at=fetched_at,
                )
            )
        return rows


def _payload_ref(payload: dict[str, Any]) -> str:
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    timezone = payload.get("timezone")
    return f"open_meteo:{latitude}:{longitude}:{timezone}:{datetime.now(UTC).date().isoformat()}"


def _is_daily_variable(variable: str) -> bool:
    return variable.endswith(("_max", "_min", "_sum")) or variable in {"precipitation_sum", "snowfall_sum"}


def _without_none(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}

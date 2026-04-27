from __future__ import annotations

from data_ingestion.core.errors import PermissionError
from data_ingestion.providers.weather.base import ProviderMetadata, WeatherRequest


class NoaaGfsProvider:
    name = "noaa_gfs"

    def get_forecast(self, request: WeatherRequest):
        raise PermissionError("direct NOAA GFS GRIB2 ingestion is reserved for V1; use Open-Meteo GFS in MVP")

    def get_observation(self, request: WeatherRequest):
        raise PermissionError("NOAA observation source requires a concrete authorized endpoint")

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name=self.name, version="reserved", capabilities=["reserved_for_v1"])

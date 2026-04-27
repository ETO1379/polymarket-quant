from __future__ import annotations

from data_ingestion.core.errors import PermissionError
from data_ingestion.providers.weather.base import ProviderMetadata, WeatherRequest


class CmaProvider:
    name = "cma"

    def get_forecast(self, request: WeatherRequest):
        raise PermissionError("CMA official API access is not configured; use Open-Meteo CMA path in MVP")

    def get_observation(self, request: WeatherRequest):
        raise PermissionError("CMA observation access requires account authorization")

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name=self.name, version="reserved", capabilities=["reserved_until_authorized"])

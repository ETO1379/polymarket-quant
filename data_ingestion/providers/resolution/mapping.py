from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data_ingestion.core.models import MarketWeatherMapping
from data_ingestion.providers.resolution.parser import ResolutionParser


@dataclass(slots=True)
class MarketWeatherMappingService:
    parser: ResolutionParser

    def build_mappings(self, markets: list[Any]) -> list[MarketWeatherMapping]:
        return [self.parser.parse(market) for market in markets]

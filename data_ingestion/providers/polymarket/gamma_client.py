from __future__ import annotations

from typing import Any

from data_ingestion.providers.polymarket.http import HttpJsonClient


class GammaClient(HttpJsonClient):
    def list_events(self, **params: Any) -> Any:
        return self.get_json("/events", params=params)

    def list_markets(self, **params: Any) -> Any:
        return self.get_json("/markets", params=params)

    def get_market(self, market_id: str) -> Any:
        return self.get_json(f"/markets/{market_id}")

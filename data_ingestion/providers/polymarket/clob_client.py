from __future__ import annotations

from typing import Any

from data_ingestion.providers.polymarket.http import HttpJsonClient


class ClobClient(HttpJsonClient):
    def get_price(self, token_id: str, side: str) -> Any:
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        params: dict[str, Any] = {"token_id": token_id, "side": normalized_side}
        return self.get_json("/price", params=params)

    def get_midpoint(self, token_id: str) -> Any:
        return self.get_json("/midpoint", params={"token_id": token_id})

    def get_spread(self, token_id: str) -> Any:
        return self.get_json("/spread", params={"token_id": token_id})

    def get_orderbook(self, token_id: str) -> Any:
        return self.get_json("/book", params={"token_id": token_id})

    def get_price_history(self, token_id: str, **params: Any) -> Any:
        return self.get_json("/prices-history", params={"market": token_id, **params})

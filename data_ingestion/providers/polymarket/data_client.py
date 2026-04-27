from __future__ import annotations

from typing import Any

from data_ingestion.providers.polymarket.http import HttpJsonClient


class DataClient(HttpJsonClient):
    def get_value(self, wallet_address: str) -> Any:
        return self.get_json("/value", params={"user": wallet_address})

    def get_positions(self, wallet_address: str) -> Any:
        return self.get_json("/positions", params={"user": wallet_address})

    def get_closed_positions(self, wallet_address: str) -> Any:
        return self.get_json("/closed-positions", params={"user": wallet_address})

    def get_trades(self, wallet_address: str) -> Any:
        return self.get_json("/trades", params={"user": wallet_address})

    def get_activity(self, wallet_address: str) -> Any:
        return self.get_json("/activity", params={"user": wallet_address})

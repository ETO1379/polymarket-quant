from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data_ingestion.core.errors import AuthenticationError
from data_ingestion.core.models import AccountSnapshotRaw, OrderRaw, PositionRaw, TradeRaw
from data_ingestion.core.time import parse_datetime, utc_now


@dataclass(slots=True)
class AccountProvider:
    data_client: Any | None = None
    wallet_address: str | None = None
    order_client: Any | None = None

    def _require_wallet(self) -> str:
        if not self.wallet_address:
            raise AuthenticationError("wallet address is required for account reads")
        return self.wallet_address

    def get_snapshot(self) -> AccountSnapshotRaw:
        wallet = self._require_wallet()
        fetched_at = utc_now()
        cash_balance: float | None = None
        total_value: float | None = None
        if self.data_client is not None and hasattr(self.data_client, "get_value"):
            payload = self.data_client.get_value(wallet)
            row = _first_payload_row(payload)
            cash_balance = _to_float(row.get("cash_balance") or row.get("cashBalance") or row.get("cash"))
            total_value = _to_float(row.get("total_value") or row.get("totalValue") or row.get("value"))
        token_balances: dict[str, float] = {}
        if self.data_client is not None:
            for position in self.get_positions():
                if position.token_id and position.size is not None:
                    token_balances[position.token_id] = position.size
        return AccountSnapshotRaw(
            wallet_address=wallet,
            cash_balance=cash_balance,
            total_value=total_value,
            token_balances=token_balances,
            fetched_at=fetched_at,
        )

    def get_positions(self) -> list[PositionRaw]:
        wallet = self._require_wallet()
        if self.data_client is None:
            return []
        payload = self.data_client.get_positions(wallet)
        rows = payload if isinstance(payload, list) else payload.get("data", [])
        fetched_at = utc_now()
        return [
            PositionRaw(
                market_id=str(row.get("market") or row.get("market_id") or ""),
                token_id=str(row.get("asset") or row.get("token_id") or ""),
                outcome=row.get("outcome"),
                size=_to_float(row.get("size")),
                avg_price=_to_float(row.get("avgPrice") or row.get("avg_price")),
                current_price=_to_float(row.get("curPrice") or row.get("current_price")),
                fetched_at=fetched_at,
            )
            for row in rows
        ]

    def get_orders(self) -> list[OrderRaw]:
        self._require_wallet()
        client = self.order_client or self.data_client
        if client is None:
            return []
        method = getattr(client, "get_orders", None) or getattr(client, "get_open_orders", None)
        if method is None:
            return []
        payload = method()
        rows = _payload_rows(payload)
        fetched_at = utc_now()
        return [
            OrderRaw(
                order_id=str(row.get("id") or row.get("order_id") or row.get("orderID") or ""),
                market_id=row.get("market") or row.get("market_id"),
                token_id=row.get("asset_id") or row.get("asset") or row.get("token_id") or row.get("tokenId"),
                side=row.get("side"),
                price=_to_float(row.get("price")),
                size=_to_float(row.get("original_size") or row.get("size")),
                filled_size=_to_float(row.get("size_matched") or row.get("filled_size")),
                status=row.get("status"),
                created_at=parse_datetime(row.get("created_at") or row.get("createdAt")),
                updated_at=parse_datetime(row.get("updated_at") or row.get("updatedAt") or row.get("last_update")),
                fetched_at=fetched_at,
            )
            for row in rows
        ]

    def get_trades(self) -> list[TradeRaw]:
        wallet = self._require_wallet()
        if self.data_client is None:
            return []
        payload = self.data_client.get_trades(wallet)
        rows = _payload_rows(payload)
        fetched_at = utc_now()
        return [
            TradeRaw(
                trade_id=str(row.get("id") or row.get("trade_id") or ""),
                order_id=row.get("order_id") or row.get("taker_order_id"),
                market_id=row.get("market") or row.get("market_id"),
                token_id=row.get("asset_id") or row.get("asset") or row.get("token_id"),
                side=row.get("side"),
                price=_to_float(row.get("price")),
                size=_to_float(row.get("size")),
                fee=_to_float(row.get("fee") or row.get("fee_rate_bps")),
                traded_at=parse_datetime(row.get("timestamp") or row.get("traded_at") or row.get("match_time")),
                fetched_at=fetched_at,
            )
            for row in rows
        ]


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _payload_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "orders", "trades", "positions", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _first_payload_row(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    rows = _payload_rows(payload)
    return rows[0] if rows else {}

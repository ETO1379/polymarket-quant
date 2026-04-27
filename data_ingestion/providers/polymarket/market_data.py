from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from data_ingestion.core.errors import SchemaChangedError
from data_ingestion.core.models import (
    MarketRaw,
    OrderBookLevel,
    OrderBookSnapshotRaw,
    PriceHistoryRaw,
    PriceSnapshotRaw,
)
from data_ingestion.core.time import parse_datetime, utc_now
from data_ingestion.services.price_backfill_service import BackfillRequest


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_float(payload: Any, *keys: str) -> float | None:
    if isinstance(payload, dict):
        for key in keys:
            value = _to_float(payload.get(key))
            if value is not None:
                return value
    return _to_float(payload)


@dataclass(slots=True)
class PriceProvider:
    clob_client: Any

    def get_price_snapshots(self, markets: list[MarketRaw] | None = None) -> list[PriceSnapshotRaw]:
        snapshots: list[PriceSnapshotRaw] = []
        for market in markets or []:
            token_ids = _field(market, "token_ids", []) or []
            outcomes = _field(market, "outcomes", []) or []
            for index, token_id in enumerate(token_ids):
                snapshots.append(self.get_price_snapshot(str(token_id), market=market, outcome=_outcome(outcomes, index)))
        return snapshots

    def get_price_snapshot(self, token_id: str, *, market: MarketRaw | None = None, outcome: str | None = None) -> PriceSnapshotRaw:
        fetched_at = utc_now()
        bid_payload = self.clob_client.get_price(token_id, "BUY")
        ask_payload = self.clob_client.get_price(token_id, "SELL")
        midpoint_payload = self.clob_client.get_midpoint(token_id)
        spread_payload = self.clob_client.get_spread(token_id)
        best_bid = _first_float(bid_payload, "price", "best_bid", "bid")
        best_ask = _first_float(ask_payload, "price", "best_ask", "ask")
        midpoint = _first_float(midpoint_payload, "mid", "midpoint")
        spread = _first_float(spread_payload, "spread")
        if best_bid is not None and best_ask is not None:
            midpoint = midpoint if midpoint is not None else (best_bid + best_ask) / 2
            spread = spread if spread is not None else best_ask - best_bid
        price = midpoint if midpoint is not None else best_ask or best_bid
        return PriceSnapshotRaw(
            market_id=str(_field(market, "market_id", "")),
            token_id=token_id,
            outcome=outcome,
            price=price,
            best_bid=best_bid,
            best_ask=best_ask,
            midpoint=midpoint,
            spread=spread,
            timestamp=parse_datetime(_field(ask_payload, "timestamp") or _field(bid_payload, "timestamp")),
            fetched_at=fetched_at,
        )


@dataclass(slots=True)
class OrderBookProvider:
    clob_client: Any
    depth_limit: int | None = 20

    def get_orderbook_snapshots(self, markets: list[MarketRaw] | None = None) -> list[OrderBookSnapshotRaw]:
        snapshots: list[OrderBookSnapshotRaw] = []
        for market in markets or []:
            for token_id in _field(market, "token_ids", []) or []:
                snapshots.append(self.get_orderbook_snapshot(str(token_id), market=market))
        return snapshots

    def get_orderbook_snapshot(self, token_id: str, *, market: MarketRaw | None = None) -> OrderBookSnapshotRaw:
        payload = self.clob_client.get_orderbook(token_id)
        if not isinstance(payload, dict):
            raise SchemaChangedError("orderbook payload must be an object")
        bids = _levels(payload.get("bids") or payload.get("buy") or [], self.depth_limit)
        asks = _levels(payload.get("asks") or payload.get("sell") or [], self.depth_limit)
        best_bid = max((level.price for level in bids), default=None)
        best_ask = min((level.price for level in asks), default=None)
        spread = round(best_ask - best_bid, 10) if best_bid is not None and best_ask is not None else None
        midpoint = round((best_bid + best_ask) / 2, 10) if best_bid is not None and best_ask is not None else None
        return OrderBookSnapshotRaw(
            snapshot_id=str(payload.get("snapshot_id") or payload.get("hash") or uuid4().hex),
            market_id=str(_field(market, "market_id", "")),
            token_id=token_id,
            bids=bids,
            asks=asks,
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            midpoint=midpoint,
            min_order_size=_to_float(payload.get("min_order_size")),
            tick_size=_to_float(payload.get("tick_size")),
            hash=payload.get("hash"),
            timestamp=parse_datetime(payload.get("timestamp")),
        )


@dataclass(slots=True)
class PriceHistoryProvider:
    clob_client: Any

    def get_price_history(self, request: BackfillRequest) -> list[PriceHistoryRaw]:
        params: dict[str, Any] = {}
        interval = _price_history_interval(request)
        fidelity_minutes = _price_history_fidelity_minutes(request)
        if interval:
            params["interval"] = interval
        elif fidelity_minutes is not None:
            params["fidelity"] = fidelity_minutes
        if request.start_time:
            params["startTs"] = int(request.start_time.timestamp())
        if request.end_time:
            params["endTs"] = int(request.end_time.timestamp())
        if request.use_max_range:
            params["interval"] = "max"
        payload = self.clob_client.get_price_history(str(request.token_id), **params)
        rows = payload if isinstance(payload, list) else payload.get("history", payload.get("data", []))
        fetched_at = utc_now()
        result: list[PriceHistoryRaw] = []
        for row in rows:
            timestamp = parse_datetime(row.get("t") or row.get("timestamp"))
            price = _to_float(row.get("p") or row.get("price"))
            if timestamp is None or price is None:
                raise SchemaChangedError("price history point missing timestamp or price")
            result.append(
                PriceHistoryRaw(
                    token_id=str(request.token_id),
                    market_id=request.market_id,
                    timestamp=timestamp,
                    price=price,
                    fidelity=request.fidelity,
                    fetched_at=fetched_at,
                )
            )
        return result


def _levels(rows: list[Any], depth_limit: int | None) -> list[OrderBookLevel]:
    result: list[OrderBookLevel] = []
    for row in rows[:depth_limit]:
        if isinstance(row, dict):
            price = _to_float(row.get("price"))
            size = _to_float(row.get("size"))
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            price = _to_float(row[0])
            size = _to_float(row[1])
        else:
            price = None
            size = None
        if price is not None and size is not None:
            result.append(OrderBookLevel(price=price, size=size))
    return result


def _outcome(outcomes: list[Any], index: int) -> str | None:
    if index < len(outcomes):
        return str(outcomes[index])
    return None


_INTERVALS = {"max", "all", "1m", "1w", "1d", "6h", "1h"}
_FIDELITY_ALIASES = {
    "1m": 1,
    "1h": 60,
    "6h": 360,
    "1d": 1440,
    "1w": 10080,
}


def _price_history_interval(request: BackfillRequest) -> str | None:
    interval = getattr(request, "interval", None)
    if interval:
        return str(interval)
    fidelity = str(getattr(request, "fidelity", "") or "")
    has_absolute_range = bool(getattr(request, "start_time", None) or getattr(request, "end_time", None))
    if fidelity in _INTERVALS and not has_absolute_range:
        return fidelity
    return None


def _price_history_fidelity_minutes(request: BackfillRequest) -> int | None:
    explicit = getattr(request, "fidelity_minutes", None)
    if explicit is not None:
        return int(explicit)
    fidelity = getattr(request, "fidelity", None)
    if isinstance(fidelity, int):
        return fidelity
    if isinstance(fidelity, str):
        if fidelity.isdigit():
            return int(fidelity)
        return _FIDELITY_ALIASES.get(fidelity)
    return None

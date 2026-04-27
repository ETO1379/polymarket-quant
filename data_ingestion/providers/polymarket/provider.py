from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from data_ingestion.core.errors import SchemaChangedError
from data_ingestion.core.models import EventRaw, MarketRaw
from data_ingestion.core.time import parse_datetime, utc_now


def _get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return default


def _as_list(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return []
        return decoded if isinstance(decoded, list) else []
    if isinstance(payload, dict):
        for key in ("data", "events", "markets"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


@dataclass(slots=True)
class PolymarketMarketProvider:
    gamma_client: Any

    def get_events(self, **params: Any) -> list[EventRaw]:
        fetched_at = utc_now()
        payload = self.gamma_client.list_events(**params)
        rows = _as_list(payload)
        return [self._parse_event(row, fetched_at) for row in rows]

    def get_markets(self, **params: Any) -> list[MarketRaw]:
        fetched_at = utc_now()
        payload = self.gamma_client.list_markets(**params)
        rows = _as_list(payload)
        return [self._parse_market(row, fetched_at) for row in rows]

    def get_market(self, market_id: str) -> MarketRaw:
        fetched_at = utc_now()
        return self._parse_market(self.gamma_client.get_market(market_id), fetched_at)

    def _parse_event(self, row: dict[str, Any], fetched_at) -> EventRaw:
        event_id = _get(row, "event_id", "id")
        if event_id is None:
            raise SchemaChangedError("event id missing")
        markets = _get(row, "markets", default=[]) or []
        market_ids = [str(_get(item, "market_id", "id", default=item)) for item in markets]
        return EventRaw(
            event_id=str(event_id),
            title=_get(row, "title"),
            slug=_get(row, "slug"),
            description=_get(row, "description"),
            category=_get(row, "category"),
            tags=[str(tag) for tag in (_get(row, "tags", default=[]) or [])],
            start_time=parse_datetime(_get(row, "start_time", "startDate")),
            end_time=parse_datetime(_get(row, "end_time", "endDate")),
            status=_get(row, "status"),
            market_ids=market_ids,
            fetched_at=fetched_at,
        )

    def _parse_market(self, row: dict[str, Any], fetched_at) -> MarketRaw:
        market_id = _get(row, "market_id", "id", "conditionId")
        if market_id is None:
            raise SchemaChangedError("market id missing")
        token_ids = _as_list(_get(row, "token_ids", "clobTokenIds", default=[]) or [])
        outcomes = _as_list(_get(row, "outcomes", default=[]) or [])
        return MarketRaw(
            market_id=str(market_id),
            event_id=_get(row, "event_id", "eventId"),
            question=str(_get(row, "question", default="") or ""),
            description=_get(row, "description"),
            rules=_get(row, "rules", "resolutionRules"),
            outcomes=[str(outcome) for outcome in outcomes],
            token_ids=[str(token_id) for token_id in token_ids],
            active=_get(row, "active"),
            closed=_get(row, "closed"),
            resolved=_get(row, "resolved"),
            end_time=parse_datetime(_get(row, "end_time", "endDate")),
            volume=_to_float(_get(row, "volume")),
            liquidity=_to_float(_get(row, "liquidity")),
            category=_get(row, "category"),
            tags=[str(tag) for tag in (_get(row, "tags", default=[]) or [])],
            fetched_at=fetched_at,
        )


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

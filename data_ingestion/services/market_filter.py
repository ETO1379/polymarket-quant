from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from data_ingestion.config.schemas import MarketFilterConfig
from data_ingestion.core.models import FilterDecision, MarketRaw


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _text_contains_any(haystack: str, needles: list[str]) -> bool:
    if not needles:
        return True
    lowered = haystack.lower()
    return any(needle.lower() in lowered for needle in needles)


@dataclass(slots=True)
class MarketFilter:
    def filter(
        self,
        events: list[Any],
        markets: list[MarketRaw],
        config: MarketFilterConfig,
    ) -> tuple[list[MarketRaw], list[FilterDecision]]:
        selected: list[MarketRaw] = []
        decisions: list[FilterDecision] = []
        allow_market_ids = set(config.market_ids or [])
        allow_event_ids = set(config.event_ids or [])

        for market in markets:
            market_id = str(_field(market, "market_id", ""))
            event_id = _field(market, "event_id")

            if market_id in allow_market_ids or (event_id is not None and event_id in allow_event_ids):
                selected.append(market)
                decisions.append(FilterDecision(market_id=market_id, kept=True, reason="allowlist"))
                continue

            reason = self._reject_reason(market, config)
            kept = reason is None
            if kept:
                selected.append(market)
            decisions.append(FilterDecision(market_id=market_id, kept=kept, reason=reason or "matched"))

        return selected, decisions

    def apply(self, events: list[Any], markets: list[MarketRaw], config: MarketFilterConfig) -> tuple[list[MarketRaw], list[FilterDecision]]:
        return self.filter(events, markets, config)

    def filter_markets(
        self,
        events: list[Any],
        markets: list[MarketRaw],
        config: MarketFilterConfig,
    ) -> tuple[list[MarketRaw], list[FilterDecision]]:
        return self.filter(events, markets, config)

    def _reject_reason(self, market: Any, config: MarketFilterConfig) -> str | None:
        if config.active is not None and _as_bool(_field(market, "active")) is not config.active:
            return "active mismatch"
        if config.closed is not None and _as_bool(_field(market, "closed")) is not config.closed:
            return "closed mismatch"
        if config.resolved is not None and _as_bool(_field(market, "resolved")) is not config.resolved:
            return "resolved mismatch"

        category = str(_field(market, "category", "") or "")
        tags = [str(tag).lower() for tag in (_field(market, "tags", []) or [])]
        if config.tags:
            wanted_tags = [tag.lower() for tag in config.tags]
            if category.lower() not in wanted_tags and not any(tag in tags for tag in wanted_tags):
                return "tag/category mismatch"

        haystack = " ".join(
            str(_field(market, key, "") or "")
            for key in ("question", "title", "description", "rules")
        )
        if not _text_contains_any(haystack, config.keywords):
            return "keyword mismatch"

        volume = _field(market, "volume")
        if config.min_volume is not None and (volume is None or float(volume) < config.min_volume):
            return "volume below minimum"

        liquidity = _field(market, "liquidity")
        if config.min_liquidity is not None and (liquidity is None or float(liquidity) < config.min_liquidity):
            return "liquidity below minimum"

        end_time = _field(market, "end_time")
        if isinstance(end_time, datetime):
            if config.end_time_after and end_time < config.end_time_after:
                return "end_time before lower bound"
            if config.end_time_before and end_time > config.end_time_before:
                return "end_time after upper bound"

        return None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(value)

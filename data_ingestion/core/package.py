from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from typing import Any

from data_ingestion.core.errors import IngestionErrorRecord
from data_ingestion.core.models import (
    AccountSnapshotRaw,
    EventRaw,
    IngestionMetrics,
    MarketRaw,
    MarketWeatherMapping,
    OrderBookSnapshotRaw,
    OrderRaw,
    PositionRaw,
    PriceHistoryRaw,
    PriceSnapshotRaw,
    RunContext,
    TradeRaw,
    WeatherRaw,
)


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return value


@dataclass(slots=True)
class RawDataPackage:
    ingestion_run_id: str
    run_context: RunContext
    started_at: datetime
    completed_at: datetime | None
    events: list[EventRaw] = field(default_factory=list)
    markets: list[MarketRaw] = field(default_factory=list)
    price_snapshots: list[PriceSnapshotRaw] = field(default_factory=list)
    orderbook_snapshots: list[OrderBookSnapshotRaw] = field(default_factory=list)
    price_history: list[PriceHistoryRaw] = field(default_factory=list)
    weather: list[WeatherRaw] = field(default_factory=list)
    market_weather_mappings: list[MarketWeatherMapping] = field(default_factory=list)
    account_snapshots: list[AccountSnapshotRaw] = field(default_factory=list)
    positions: list[PositionRaw] = field(default_factory=list)
    orders: list[OrderRaw] = field(default_factory=list)
    trades: list[TradeRaw] = field(default_factory=list)
    errors: list[IngestionErrorRecord] = field(default_factory=list)
    metrics: IngestionMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        return _plain(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

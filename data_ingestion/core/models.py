from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from data_ingestion.core.time import utc_now


@dataclass(slots=True)
class RunContext:
    ingestion_run_id: str
    started_at: datetime
    config_version: str | None = None
    provider_versions: dict[str, str] = field(default_factory=dict)
    request_scope: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = True
    live_trading_allowed: bool = False
    mode: str = "dry_run"


@dataclass(slots=True)
class EventRaw:
    event_id: str
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None
    market_ids: list[str] = field(default_factory=list)
    source: str = "polymarket_gamma"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class MarketRaw:
    market_id: str
    event_id: str | None = None
    question: str = ""
    description: str | None = None
    rules: str | None = None
    outcomes: list[str] = field(default_factory=list)
    token_ids: list[str] = field(default_factory=list)
    active: bool | None = None
    closed: bool | None = None
    resolved: bool | None = None
    end_time: datetime | None = None
    volume: float | None = None
    liquidity: float | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str = "polymarket_gamma"
    raw_payload_ref: str | None = None
    raw_data_ref: str | None = None
    fetched_at: datetime = field(default_factory=utc_now)
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class PriceSnapshotRaw:
    market_id: str
    token_id: str
    outcome: str | None = None
    price: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    midpoint: float | None = None
    spread: float | None = None
    timestamp: datetime | None = None
    source: str = "polymarket_clob"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class OrderBookLevel:
    price: float
    size: float


@dataclass(slots=True)
class OrderBookSnapshotRaw:
    snapshot_id: str
    market_id: str
    token_id: str
    bids: list[OrderBookLevel] = field(default_factory=list)
    asks: list[OrderBookLevel] = field(default_factory=list)
    best_bid: float | None = None
    best_ask: float | None = None
    spread: float | None = None
    midpoint: float | None = None
    min_order_size: float | None = None
    tick_size: float | None = None
    hash: str | None = None
    timestamp: datetime | None = None
    source: str = "polymarket_clob"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class PriceHistoryRaw:
    token_id: str
    timestamp: datetime
    price: float
    fidelity: str
    market_id: str | None = None
    source: str = "polymarket_clob"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class AccountSnapshotRaw:
    account_id: str | None = None
    wallet_address: str | None = None
    cash_balance: float | None = None
    total_value: float | None = None
    token_balances: dict[str, float] = field(default_factory=dict)
    source: str = "polymarket_account"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class PositionRaw:
    market_id: str
    token_id: str
    outcome: str | None = None
    size: float | None = None
    avg_price: float | None = None
    current_price: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    source: str = "polymarket_account"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class OrderRaw:
    order_id: str
    market_id: str | None = None
    token_id: str | None = None
    side: str | None = None
    price: float | None = None
    size: float | None = None
    filled_size: float | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source: str = "polymarket_account"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class TradeRaw:
    trade_id: str
    order_id: str | None = None
    market_id: str | None = None
    token_id: str | None = None
    side: str | None = None
    price: float | None = None
    size: float | None = None
    fee: float | None = None
    traded_at: datetime | None = None
    source: str = "polymarket_account"
    fetched_at: datetime = field(default_factory=utc_now)
    raw_data_ref: str | None = None
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class WeatherRaw:
    source: str
    provider_type: str
    location_id: str
    lat: float
    lon: float
    timezone: str
    variable: str
    unit: str
    value: float | None = None
    model: str | None = None
    run_time: datetime | None = None
    forecast_time: datetime | None = None
    observed_time: datetime | None = None
    station_id: str | None = None
    raw_data_ref: str | None = None
    fetched_at: datetime = field(default_factory=utc_now)
    request_id: str | None = None
    ingestion_run_id: str | None = None


@dataclass(slots=True)
class MarketWeatherMapping:
    market_id: str
    event_id: str | None = None
    location_id: str | None = None
    location_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    station_id: str | None = None
    resolution_rules_raw_ref: str | None = None
    resolution_source_name: str | None = None
    resolution_source_url: str | None = None
    forecast_provider: str | None = None
    forecast_model: str | None = None
    observation_provider: str | None = None
    target_variable: str | None = None
    target_date: date | None = None
    target_time_window: str | None = None
    timezone: str | None = None
    unit: str | None = None
    parsing_status: str = "manual_review"
    parsing_reason: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class IngestionMetrics:
    ingestion_run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    events_count: int = 0
    markets_count: int = 0
    filtered_markets_count: int = 0
    price_success_count: int = 0
    price_error_count: int = 0
    orderbook_success_count: int = 0
    orderbook_error_count: int = 0
    weather_success_count: int = 0
    weather_error_count: int = 0
    account_success: bool = False
    error_count_by_type: dict[str, int] = field(default_factory=dict)
    duration_ms_by_provider: dict[str, float] = field(default_factory=dict)
    rate_limit_count_by_provider: dict[str, int] = field(default_factory=dict)
    schema_error_count_by_provider: dict[str, int] = field(default_factory=dict)
    stale_count_by_data_type: dict[str, int] = field(default_factory=dict)
    skipped_market_count_by_reason: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class FilterDecision:
    market_id: str
    kept: bool
    reason: str

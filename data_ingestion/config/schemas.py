from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MarketFilterConfig:
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    active: bool | None = None
    closed: bool | None = None
    resolved: bool | None = None
    min_volume: float | None = None
    min_liquidity: float | None = None
    market_ids: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)
    end_time_after: datetime | None = None
    end_time_before: datetime | None = None


@dataclass(slots=True)
class PolymarketConfig:
    api_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    data_base_url: str = "https://data-api.polymarket.com"
    request_timeout_seconds: float = 10
    retry_times: int = 3
    rate_limit_per_second: float = 2
    price_refresh_interval_seconds: int = 60
    orderbook_depth_limit: int | None = 20
    market_filters: MarketFilterConfig = field(default_factory=MarketFilterConfig)


@dataclass(slots=True)
class AccountConfig:
    wallet_address: str | None = None
    api_key_ref: str | None = "POLYMARKET_API_KEY"
    private_key_ref: str | None = "POLYMARKET_PRIVATE_KEY"
    account_refresh_interval_seconds: int = 60
    include_orders: bool = True
    include_trades: bool = True
    include_deposit_withdraw: bool = False


@dataclass(slots=True)
class WeatherConfig:
    enabled_providers: list[str] = field(default_factory=lambda: ["open_meteo"])
    default_forecast_provider: str = "open_meteo"
    fallback_provider: str | None = None
    forecast_horizon_days: int = 7
    observation_window_days: int = 3
    timezone_policy: str = "resolution_timezone_first"
    resolution_source_policy: str = "manual_review_if_unclear"
    variables: list[str] = field(default_factory=lambda: ["temperature_2m", "precipitation", "wind_speed_10m"])


@dataclass(slots=True)
class PriceHistoryConfig:
    enabled: bool = True
    default_fidelity: str = "1h"
    max_backfill_days: int = 30
    batch_size: int = 20
    allow_max_range: bool = False


@dataclass(slots=True)
class IngestionConfig:
    dry_run: bool = True
    live_trading_allowed: bool = False
    data_ingestion: dict[str, Any] = field(default_factory=dict)
    polymarket: PolymarketConfig = field(default_factory=PolymarketConfig)
    account: AccountConfig = field(default_factory=AccountConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    price_history: PriceHistoryConfig = field(default_factory=PriceHistoryConfig)
    config_version: str = "default"

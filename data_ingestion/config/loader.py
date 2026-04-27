from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import Any

from data_ingestion.config.schemas import (
    AccountConfig,
    IngestionConfig,
    MarketFilterConfig,
    PolymarketConfig,
    PriceHistoryConfig,
    WeatherConfig,
)


def load_ingestion_config(path: str | Path) -> IngestionConfig:
    payload = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    data = payload.get("data_ingestion", payload)
    polymarket_data = data.get("polymarket", {})
    market_filter_data = polymarket_data.get("market_filters", {})
    account_data = dict(data.get("account", {}))
    if "wallet_address" in account_data:
        account_data["wallet_address"] = _resolve_env_placeholder(account_data["wallet_address"])
    return IngestionConfig(
        dry_run=data.get("dry_run", True),
        live_trading_allowed=data.get("live_trading_allowed", False),
        config_version=data.get("config_version", "file"),
        data_ingestion=data,
        polymarket=PolymarketConfig(
            **_without_keys(polymarket_data, {"market_filters"}),
            market_filters=MarketFilterConfig(**market_filter_data),
        ),
        account=AccountConfig(**account_data),
        weather=WeatherConfig(**data.get("weather", {})),
        price_history=PriceHistoryConfig(**data.get("price_history", {})),
    )


def _without_keys(data: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key not in keys}


_ENV_PLACEHOLDER = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def _resolve_env_placeholder(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    match = _ENV_PLACEHOLDER.match(value.strip())
    if not match:
        return value
    resolved = os.getenv(match.group(1))
    return resolved or None

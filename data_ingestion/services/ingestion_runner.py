from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import uuid4

from data_ingestion.config.schemas import IngestionConfig
from data_ingestion.core.errors import AuthenticationError, IngestionErrorRecord
from data_ingestion.core.models import IngestionMetrics, RunContext
from data_ingestion.core.package import RawDataPackage
from data_ingestion.core.time import utc_now
from data_ingestion.ports.monitoring_sink import NoopMonitoringSink
from data_ingestion.ports.storage_writer import NoopStorageWriter
from data_ingestion.providers.resolution.mapping import MarketWeatherMappingService
from data_ingestion.providers.resolution.parser import ResolutionParser
from data_ingestion.providers.weather.open_meteo import WeatherRequestBuilder
from data_ingestion.services.market_filter import MarketFilter


class IngestionRunner:
    def __init__(
        self,
        *,
        config: IngestionConfig,
        market_provider: Any | None = None,
        price_provider: Any | None = None,
        orderbook_provider: Any | None = None,
        weather_provider: Any | None = None,
        account_provider: Any | None = None,
        storage_writer: Any | None = None,
        monitoring_sink: Any | None = None,
    ) -> None:
        self.config = config
        self.market_provider = market_provider
        self.price_provider = price_provider
        self.orderbook_provider = orderbook_provider
        self.weather_provider = weather_provider
        self.account_provider = account_provider
        self.storage_writer = storage_writer or NoopStorageWriter()
        self.monitoring_sink = monitoring_sink or NoopMonitoringSink()
        self.market_filter = MarketFilter()
        self.mapping_service = MarketWeatherMappingService(ResolutionParser())
        self.weather_request_builder = WeatherRequestBuilder()

    def run_once(self) -> RawDataPackage:
        started_at = utc_now()
        ingestion_run_id = f"run_{uuid4().hex}"
        live_allowed = bool(getattr(self.config, "live_trading_allowed", False))
        dry_run = bool(getattr(self.config, "dry_run", True))
        run_context = RunContext(
            ingestion_run_id=ingestion_run_id,
            started_at=started_at,
            config_version=getattr(self.config, "config_version", "default"),
            dry_run=dry_run,
            live_trading_allowed=live_allowed,
            mode="live" if live_allowed and not dry_run else "dry_run",
        )
        errors: list[IngestionErrorRecord] = []
        live_requested = run_context.live_trading_allowed and not run_context.dry_run
        if live_requested and self.account_provider is None:
            errors.append(
                IngestionErrorRecord.from_exception(
                    AuthenticationError("account provider is required for live trading"),
                    provider="account",
                )
            )
            _downgrade_to_dry_run(run_context)

        events = self._safe_call_list(self.market_provider, ("get_events", "list_events"), errors, "market")
        markets = self._safe_call_list(self.market_provider, ("get_markets", "list_markets"), errors, "market")
        filtered_markets = markets
        decisions = []
        if markets:
            try:
                filtered_markets, decisions = self.market_filter.filter(
                    events,
                    markets,
                    self.config.polymarket.market_filters,
                )
            except Exception as exc:
                errors.append(IngestionErrorRecord.from_exception(exc, provider="market_filter"))
                filtered_markets = []

        market_weather_mappings = []
        if filtered_markets:
            market_weather_mappings = self.mapping_service.build_mappings(filtered_markets)

        price_snapshots = self._safe_call_list(
            self.price_provider,
            ("get_price_snapshots", "get_prices"),
            errors,
            "price",
            filtered_markets,
        )
        orderbook_snapshots = self._safe_call_list(
            self.orderbook_provider or self.price_provider,
            ("get_orderbook_snapshots", "get_orderbooks"),
            errors,
            "orderbook",
            filtered_markets,
        )
        weather = self._collect_weather(market_weather_mappings, errors, run_context)

        account_snapshots: list[Any] = []
        positions: list[Any] = []
        orders: list[Any] = []
        trades: list[Any] = []
        account_success = False
        if self.account_provider is not None:
            try:
                snapshot = self._call_first(self.account_provider, ("get_snapshot", "get_balance", "get_account_snapshot"))
                if snapshot is not None:
                    account_snapshots = snapshot if isinstance(snapshot, list) else [snapshot]
                if live_requested and not _has_usable_account_snapshot(account_snapshots):
                    raise AuthenticationError("usable account snapshot is required for live trading")
                positions = self._maybe_call_list(self.account_provider, ("get_positions", "list_positions"))
                orders = self._maybe_call_list(self.account_provider, ("get_orders", "list_orders", "get_open_orders"))
                trades = self._maybe_call_list(self.account_provider, ("get_trades", "list_trades", "get_fills"))
                account_success = True
            except Exception as exc:
                errors.append(IngestionErrorRecord.from_exception(exc, provider="account"))
                _downgrade_to_dry_run(run_context)

        completed_at = utc_now()
        error_counts = Counter(error.error_type for error in errors)
        metrics = IngestionMetrics(
            ingestion_run_id=ingestion_run_id,
            started_at=started_at,
            completed_at=completed_at,
            events_count=len(events),
            markets_count=len(markets),
            filtered_markets_count=len(filtered_markets),
            price_success_count=len(price_snapshots),
            orderbook_success_count=len(orderbook_snapshots),
            weather_success_count=len(weather),
            account_success=account_success,
            error_count_by_type=dict(error_counts),
            skipped_market_count_by_reason=_skipped_reasons(decisions),
        )
        package = RawDataPackage(
            ingestion_run_id=ingestion_run_id,
            run_context=run_context,
            started_at=started_at,
            completed_at=completed_at,
            events=events,
            markets=markets,
            price_snapshots=price_snapshots,
            orderbook_snapshots=orderbook_snapshots,
            price_history=[],
            weather=weather,
            market_weather_mappings=market_weather_mappings,
            account_snapshots=account_snapshots,
            positions=positions,
            orders=orders,
            trades=trades,
            errors=errors,
            metrics=metrics,
        )
        self._emit(package)
        return package

    def _safe_call_list(
        self,
        provider: Any | None,
        methods: tuple[str, ...],
        errors: list[IngestionErrorRecord],
        provider_name: str,
        *args: Any,
    ) -> list[Any]:
        if provider is None:
            return []
        try:
            return self._maybe_call_list(provider, methods, *args)
        except Exception as exc:
            errors.append(IngestionErrorRecord.from_exception(exc, provider=provider_name))
            return []

    def _maybe_call_list(self, provider: Any, methods: tuple[str, ...], *args: Any) -> list[Any]:
        result = self._call_first(provider, methods, *args)
        if result is None:
            return []
        return result if isinstance(result, list) else [result]

    def _call_first(self, provider: Any, methods: tuple[str, ...], *args: Any) -> Any:
        for method_name in methods:
            method = getattr(provider, method_name, None)
            if method is not None:
                try:
                    return method(*args)
                except TypeError:
                    return method()
        return []

    def _collect_weather(self, mappings: list[Any], errors: list[IngestionErrorRecord], run_context: RunContext) -> list[Any]:
        if self.weather_provider is None:
            return []
        rows: list[Any] = []
        for mapping in mappings:
            if getattr(mapping, "parsing_status", None) != "parsed":
                continue
            try:
                request = self.weather_request_builder.build_forecast_request(
                    mapping,
                    allow_live_trading=run_context.live_trading_allowed,
                )
                forecast = self.weather_provider.get_forecast(request)
                rows.extend(forecast if isinstance(forecast, list) else [forecast])
            except Exception as exc:
                errors.append(
                    IngestionErrorRecord.from_exception(
                        exc,
                        provider="weather",
                        market_id=getattr(mapping, "market_id", None),
                    )
                )
        return rows

    def _emit(self, package: RawDataPackage) -> None:
        save = getattr(self.storage_writer, "save_raw_package", None)
        if save:
            save(package)
        emit_metrics = getattr(self.monitoring_sink, "emit_metrics", None)
        if emit_metrics and package.metrics is not None:
            emit_metrics(package.metrics)
        emit_error = getattr(self.monitoring_sink, "emit_error", None)
        if emit_error:
            for error in package.errors:
                emit_error(error)


def _skipped_reasons(decisions: list[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for decision in decisions:
        if not getattr(decision, "kept", False):
            counts[str(getattr(decision, "reason", "unknown"))] += 1
    return dict(counts)


def _downgrade_to_dry_run(run_context: RunContext) -> None:
    run_context.live_trading_allowed = False
    run_context.dry_run = True
    run_context.mode = "dry_run"


def _has_usable_account_snapshot(account_snapshots: list[Any]) -> bool:
    if not account_snapshots:
        return False
    for snapshot in account_snapshots:
        cash_balance = _field(snapshot, "cash_balance")
        total_value = _field(snapshot, "total_value")
        token_balances = _field(snapshot, "token_balances", {})
        wallet_address = _field(snapshot, "wallet_address") or _field(snapshot, "account_id")
        if wallet_address and (cash_balance is not None or total_value is not None or bool(token_balances)):
            return True
    return False


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

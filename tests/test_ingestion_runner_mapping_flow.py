from __future__ import annotations

from datetime import timedelta

from conftest import UTC_NOW, get_field, import_attr, make_model, optional_attr


class MarketProvider:
    def __init__(self, market):
        self.market = market

    def get_events(self):
        return []

    def get_markets(self):
        return [self.market]


class WeatherProvider:
    def get_forecast(self, request):
        WeatherRaw = import_attr("data_ingestion.core.models", "WeatherRaw")
        return [
            WeatherRaw(
                source="open_meteo",
                provider_type="forecast",
                model=request.model,
                forecast_time=UTC_NOW + timedelta(hours=1),
                location_id=request.location_id,
                lat=request.lat,
                lon=request.lon,
                timezone=request.timezone,
                variable=request.variable,
                value=82.0,
                unit="F",
                fetched_at=UTC_NOW,
            )
        ]


class EmptyAccountProvider:
    def get_snapshot(self):
        return []

    def get_positions(self):
        return []

    def get_orders(self):
        return []

    def get_trades(self):
        return []


def test_runner_generates_mapping_and_fetches_weather_for_parsed_market(market_fixture):
    IngestionRunner = import_attr("data_ingestion.services.ingestion_runner", "IngestionRunner")
    IngestionConfig = optional_attr("data_ingestion.config.schemas", "IngestionConfig")
    MarketFilterConfig = optional_attr("data_ingestion.config.schemas", "MarketFilterConfig")

    config = make_model(IngestionConfig, dry_run=True, live_trading_allowed=False)
    config.polymarket.market_filters = make_model(
        MarketFilterConfig,
        tags=["weather"],
        keywords=["Central Park"],
        active=True,
        closed=False,
        resolved=False,
    )

    package = IngestionRunner(
        config=config,
        market_provider=MarketProvider(market_fixture),
        weather_provider=WeatherProvider(),
        account_provider=EmptyAccountProvider(),
    ).run_once()

    mappings = get_field(package, "market_weather_mappings", [])
    assert len(mappings) == 1
    assert get_field(mappings[0], "parsing_status") == "parsed"
    assert get_field(package, "weather", [])
    assert get_field(package.metrics, "filtered_markets_count") == 1

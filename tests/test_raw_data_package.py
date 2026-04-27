from __future__ import annotations

import json

from conftest import UTC_NOW, import_attr, make_model, optional_attr, to_plain


def test_raw_data_package_is_json_serializable():
    RawDataPackage = import_attr("data_ingestion.core.package", "RawDataPackage")
    RunContext = optional_attr("data_ingestion.core.models", "RunContext")
    IngestionMetrics = optional_attr("data_ingestion.core.models", "IngestionMetrics")

    run_context = make_model(
        RunContext,
        ingestion_run_id="run_test_001",
        started_at=UTC_NOW,
        config_version="test",
        provider_versions={"polymarket": "fake", "open_meteo": "fake"},
        request_scope={"market_ids": ["m_weather_nyc"]},
        dry_run=True,
        live_trading_allowed=False,
    )
    metrics = make_model(
        IngestionMetrics,
        ingestion_run_id="run_test_001",
        started_at=UTC_NOW,
        completed_at=UTC_NOW,
        events_count=0,
        markets_count=1,
        filtered_markets_count=1,
        account_success=False,
        error_count_by_type={"AuthenticationError": 1},
    )
    package = RawDataPackage(
        ingestion_run_id="run_test_001",
        run_context=run_context,
        started_at=UTC_NOW,
        completed_at=UTC_NOW,
        events=[],
        markets=[],
        price_snapshots=[],
        orderbook_snapshots=[],
        price_history=[],
        weather=[],
        market_weather_mappings=[],
        account_snapshots=[],
        positions=[],
        orders=[],
        trades=[],
        errors=[],
        metrics=metrics,
    )

    if hasattr(package, "to_json"):
        payload = package.to_json()
        json.loads(payload)
        return

    plain = to_plain(package)
    json.dumps(plain, default=str)

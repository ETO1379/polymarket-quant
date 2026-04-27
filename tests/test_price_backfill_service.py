from __future__ import annotations

from datetime import timedelta

import pytest

from conftest import UTC_NOW, call_first, import_attr, make_model, optional_attr


def test_price_backfill_service_rejects_max_range_when_not_allowed():
    PriceBackfillService = import_attr("data_ingestion.services.price_backfill_service", "PriceBackfillService")
    BackfillRequest = optional_attr("data_ingestion.services.price_backfill_service", "BackfillRequest")

    request = make_model(
        BackfillRequest,
        market_id="m_weather_nyc",
        token_id="token_yes",
        start_time=None,
        end_time=None,
        fidelity="max",
        use_max_range=True,
    )

    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        call_first(
            PriceBackfillService(max_backfill_days=30, allow_max_range=False),
            ("validate_request", "backfill"),
            request,
        )


def test_price_backfill_service_rejects_interval_with_absolute_range():
    PriceBackfillService = import_attr("data_ingestion.services.price_backfill_service", "PriceBackfillService")
    BackfillRequest = optional_attr("data_ingestion.services.price_backfill_service", "BackfillRequest")

    request = make_model(
        BackfillRequest,
        market_id="m_weather_nyc",
        token_id="token_yes",
        start_time=UTC_NOW - timedelta(days=1),
        end_time=UTC_NOW,
        fidelity="1",
        interval="1h",
        use_max_range=False,
    )

    with pytest.raises((ValueError, RuntimeError)):
        call_first(
            PriceBackfillService(max_backfill_days=30, allow_max_range=False),
            ("validate_request", "backfill"),
            request,
        )


def test_price_backfill_service_rejects_range_longer_than_configured_limit():
    PriceBackfillService = import_attr("data_ingestion.services.price_backfill_service", "PriceBackfillService")
    BackfillRequest = optional_attr("data_ingestion.services.price_backfill_service", "BackfillRequest")

    request = make_model(
        BackfillRequest,
        market_id="m_weather_nyc",
        token_id="token_yes",
        start_time=UTC_NOW - timedelta(days=31),
        end_time=UTC_NOW,
        fidelity="1h",
        use_max_range=False,
    )

    with pytest.raises((ValueError, RuntimeError)):
        call_first(
            PriceBackfillService(max_backfill_days=30, allow_max_range=False),
            ("validate_request", "backfill"),
            request,
        )


def test_price_backfill_service_requires_token_id():
    PriceBackfillService = import_attr("data_ingestion.services.price_backfill_service", "PriceBackfillService")
    BackfillRequest = optional_attr("data_ingestion.services.price_backfill_service", "BackfillRequest")

    request = make_model(
        BackfillRequest,
        market_id="m_weather_nyc",
        token_id=None,
        start_time=UTC_NOW - timedelta(days=1),
        end_time=UTC_NOW,
        fidelity="1h",
        use_max_range=False,
    )

    with pytest.raises((ValueError, RuntimeError)):
        call_first(
            PriceBackfillService(max_backfill_days=30, allow_max_range=False),
            ("validate_request", "backfill"),
            request,
        )

from __future__ import annotations

from datetime import timedelta

from conftest import UTC_NOW, call_first, get_field, import_attr


def test_freshness_check_marks_stale_when_source_timestamp_exceeds_max_age():
    FreshnessCheck = import_attr("data_ingestion.services.freshness", "FreshnessCheck")

    result = call_first(
        FreshnessCheck(),
        ("check", "evaluate"),
        data_type="price",
        market_id="m_weather_nyc",
        source_timestamp=UTC_NOW - timedelta(minutes=6),
        fetched_at=UTC_NOW,
        max_age_seconds=300,
    )

    assert get_field(result, "data_type") == "price"
    assert get_field(result, "market_id") == "m_weather_nyc"
    assert get_field(result, "is_stale") is True
    assert "stale" in str(get_field(result, "reason", "")).lower() or "过期" in str(get_field(result, "reason", ""))


def test_freshness_check_keeps_recent_data_fresh():
    FreshnessCheck = import_attr("data_ingestion.services.freshness", "FreshnessCheck")

    result = call_first(
        FreshnessCheck(),
        ("check", "evaluate"),
        data_type="weather_forecast",
        market_id="m_weather_nyc",
        source_timestamp=UTC_NOW - timedelta(minutes=2),
        fetched_at=UTC_NOW,
        max_age_seconds=300,
    )

    assert get_field(result, "is_stale") is False

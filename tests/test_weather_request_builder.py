from __future__ import annotations

import pytest

from conftest import call_first, get_field, import_attr


def test_weather_request_builder_builds_request_only_for_parsed_mapping(parsed_mapping):
    WeatherRequestBuilder = import_attr("data_ingestion.providers.weather.open_meteo", "WeatherRequestBuilder")

    request = call_first(
        WeatherRequestBuilder(),
        ("build_forecast_request", "build_request", "build"),
        parsed_mapping,
        allow_live_trading=True,
    )

    assert get_field(request, "location_id") == "nyc_central_park"
    assert get_field(request, "lat") == parsed_mapping.lat
    assert get_field(request, "lon") == parsed_mapping.lon
    assert get_field(request, "timezone") == "America/New_York"
    assert get_field(request, "variable") == "temperature_2m_max"


def test_weather_request_builder_rejects_manual_review_mapping_for_live_trading(parsed_mapping):
    WeatherRequestBuilder = import_attr("data_ingestion.providers.weather.open_meteo", "WeatherRequestBuilder")
    parsed_mapping.parsing_status = "manual_review"
    parsed_mapping.parsing_reason = "resolution source is unclear"

    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        call_first(
            WeatherRequestBuilder(),
            ("build_forecast_request", "build_request", "build"),
            parsed_mapping,
            allow_live_trading=True,
        )

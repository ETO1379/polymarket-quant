from __future__ import annotations

from conftest import get_field, import_attr


def test_resolution_parser_extracts_clear_weather_mapping(market_fixture):
    ResolutionParser = import_attr("data_ingestion.providers.resolution.parser", "ResolutionParser")

    mapping = ResolutionParser().parse(market_fixture)

    assert get_field(mapping, "market_id") == "m_weather_nyc"
    assert get_field(mapping, "parsing_status") == "parsed"
    assert get_field(mapping, "resolution_source_name")
    assert "weather" in get_field(mapping, "resolution_source_name").lower() or "national" in get_field(mapping, "resolution_source_name").lower()
    assert get_field(mapping, "target_variable") in {"temperature_2m_max", "max_temperature", "temperature"}
    assert get_field(mapping, "timezone") in {"America/New_York", "US/Eastern"}
    assert get_field(mapping, "unit") in {"F", "fahrenheit"}


def test_resolution_parser_marks_unclear_rules_for_manual_review(market_fixture):
    ResolutionParser = import_attr("data_ingestion.providers.resolution.parser", "ResolutionParser")

    unclear_market = {
        **market_fixture,
        "market_id": "m_unclear",
        "rules": "This market resolves based on official sources after the event.",
        "description": "Ambiguous weather resolution source.",
    }

    mapping = ResolutionParser().parse(unclear_market)

    assert get_field(mapping, "parsing_status") in {"manual_review", "failed"}
    assert get_field(mapping, "resolution_source_name") in {None, ""}
    assert get_field(mapping, "parsing_reason")

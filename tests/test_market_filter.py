from __future__ import annotations

from datetime import timedelta

from conftest import UTC_NOW, call_first, get_field, import_attr, make_model, optional_attr


def test_market_filter_combines_status_keyword_volume_and_whitelist(market_fixture):
    MarketFilter = import_attr("data_ingestion.services.market_filter", "MarketFilter")
    MarketFilterConfig = optional_attr("data_ingestion.config.schemas", "MarketFilterConfig")
    MarketRaw = optional_attr("data_ingestion.core.models", "MarketRaw")

    keep = make_model(MarketRaw, **market_fixture)
    closed = make_model(MarketRaw, **{**market_fixture, "market_id": "m_closed", "closed": True})
    low_liquidity = make_model(
        MarketRaw,
        **{**market_fixture, "market_id": "m_low_liq", "liquidity": 10.0},
    )
    whitelisted = make_model(
        MarketRaw,
        **{
            **market_fixture,
            "market_id": "m_allowlisted",
            "question": "Non weather allowlisted market",
            "tags": [],
            "liquidity": 1.0,
        },
    )

    config = make_model(
        MarketFilterConfig,
        tags=["weather"],
        keywords=["Central Park"],
        active=True,
        closed=False,
        resolved=False,
        min_volume=1000,
        min_liquidity=100,
        market_ids=["m_allowlisted"],
        event_ids=[],
        end_time_after=UTC_NOW,
        end_time_before=UTC_NOW + timedelta(days=7),
    )

    result = call_first(MarketFilter(), ("filter", "apply", "filter_markets"), [], [keep, closed, low_liquidity, whitelisted], config)
    selected, decisions = result if isinstance(result, tuple) else (result, [])

    selected_ids = {get_field(market, "market_id") for market in selected}
    assert selected_ids == {"m_weather_nyc", "m_allowlisted"}

    if decisions:
        decision_by_id = {get_field(d, "market_id"): d for d in decisions}
        assert get_field(decision_by_id["m_closed"], "kept") is False
        assert "closed" in str(get_field(decision_by_id["m_closed"], "reason", "")).lower()
        assert get_field(decision_by_id["m_low_liq"], "kept") is False

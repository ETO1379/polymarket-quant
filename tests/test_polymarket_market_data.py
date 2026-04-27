from __future__ import annotations

from datetime import timedelta

from conftest import UTC_NOW, get_field, import_attr, make_model, optional_attr


class FakeClobClient:
    def __init__(self):
        self.price_calls = []
        self.history_calls = []

    def get_price(self, token_id, side):
        self.price_calls.append((token_id, side))
        price = "0.41" if side == "BUY" else "0.43"
        return {"price": price, "timestamp": UTC_NOW.isoformat()}

    def get_midpoint(self, token_id):
        return {"mid": "0.42"}

    def get_spread(self, token_id):
        return {"spread": "0.02"}

    def get_orderbook(self, token_id):
        return {
            "hash": "book_hash",
            "bids": [{"price": "0.41", "size": "10"}],
            "asks": [{"price": "0.43", "size": "11"}],
            "timestamp": UTC_NOW.isoformat(),
        }

    def get_price_history(self, token_id, **params):
        self.history_calls.append((token_id, params))
        return {"history": [{"t": int((UTC_NOW - timedelta(hours=1)).timestamp()), "p": "0.40"}]}


def test_price_and_orderbook_providers_parse_clob_payloads(market_fixture):
    PriceProvider = import_attr("data_ingestion.providers.polymarket.market_data", "PriceProvider")
    OrderBookProvider = import_attr("data_ingestion.providers.polymarket.market_data", "OrderBookProvider")
    MarketRaw = optional_attr("data_ingestion.core.models", "MarketRaw")

    market = make_model(MarketRaw, **market_fixture)
    clob_client = FakeClobClient()
    price_rows = PriceProvider(clob_client).get_price_snapshots([market])
    book_rows = OrderBookProvider(FakeClobClient()).get_orderbook_snapshots([market])

    assert len(price_rows) == 2
    assert get_field(price_rows[0], "best_bid") == 0.41
    assert get_field(price_rows[0], "best_ask") == 0.43
    assert get_field(price_rows[0], "price") == 0.42
    assert clob_client.price_calls[:2] == [("token_yes", "BUY"), ("token_yes", "SELL")]
    assert len(book_rows) == 2
    assert get_field(book_rows[0], "spread") == 0.02


def test_price_history_provider_matches_backfill_service_protocol(market_fixture):
    PriceHistoryProvider = import_attr("data_ingestion.providers.polymarket.market_data", "PriceHistoryProvider")
    PriceBackfillService = import_attr("data_ingestion.services.price_backfill_service", "PriceBackfillService")
    BackfillRequest = import_attr("data_ingestion.services.price_backfill_service", "BackfillRequest")

    request = BackfillRequest(
        market_id="m_weather_nyc",
        token_id="token_yes",
        start_time=UTC_NOW - timedelta(days=1),
        end_time=UTC_NOW,
        fidelity="1h",
    )
    clob_client = FakeClobClient()
    rows = PriceBackfillService(provider=PriceHistoryProvider(clob_client)).backfill(request)

    assert len(rows) == 1
    assert get_field(rows[0], "price") == 0.40
    assert clob_client.history_calls[0][1]["fidelity"] == 60


def test_market_provider_parses_gamma_json_string_arrays():
    PolymarketMarketProvider = import_attr("data_ingestion.providers.polymarket.provider", "PolymarketMarketProvider")

    market = PolymarketMarketProvider(None)._parse_market(
        {
            "id": "m1",
            "question": "Question",
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["token_yes", "token_no"]',
        },
        UTC_NOW,
    )

    assert get_field(market, "outcomes") == ["Yes", "No"]
    assert get_field(market, "token_ids") == ["token_yes", "token_no"]

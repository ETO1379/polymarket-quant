from __future__ import annotations

from datetime import UTC, datetime, timedelta


NOW = datetime(2026, 4, 26, 4, 0, tzinfo=UTC)


POLYMARKET_WEATHER_MARKET = {
    "id": "m_weather_nyc",
    "event_id": "e_weather_apr",
    "question": "Will NYC Central Park record over 80F on April 26?",
    "description": "Weather market for New York City.",
    "rules": (
        "This market resolves according to the National Weather Service "
        "Central Park station observation for April 26, 2026, in America/New_York."
    ),
    "outcomes": ["Yes", "No"],
    "clobTokenIds": ["token_yes", "token_no"],
    "active": True,
    "closed": False,
    "resolved": False,
    "endDate": (NOW + timedelta(days=1)).isoformat(),
    "volume": 5000,
    "liquidity": 2000,
    "tags": ["weather", "temperature"],
}


OPEN_METEO_FORECAST = {
    "latitude": 40.78,
    "longitude": -73.97,
    "timezone": "America/New_York",
    "hourly_units": {"temperature_2m": "F"},
    "hourly": {
        "time": ["2026-04-26T12:00"],
        "temperature_2m": [82.1],
    },
}


PRICE_HISTORY = [
    {"t": int((NOW - timedelta(hours=2)).timestamp()), "p": 0.42},
    {"t": int((NOW - timedelta(hours=1)).timestamp()), "p": 0.46},
]

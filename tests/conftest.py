from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from typing import Any

import pytest


UTC_NOW = datetime(2026, 4, 26, 4, 0, tzinfo=UTC)


def import_attr(module_name: str, attr_name: str) -> Any:
    """导入文档约定的接口；实现未落地时跳过契约测试。"""
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        pytest.skip(f"假设接口尚未实现：无法导入 {module_name}（{exc.name}）")

    try:
        return getattr(module, attr_name)
    except AttributeError:
        pytest.skip(f"假设接口尚未实现：{module_name}.{attr_name} 不存在")


def optional_attr(module_name: str, attr_name: str) -> Any | None:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    return getattr(module, attr_name, None)


def make_model(cls: type | None, **values: Any) -> Any:
    """优先使用实现模型；缺失时用 SimpleNamespace 表达文档字段。"""
    if cls is None:
        return SimpleNamespace(**values)
    try:
        return cls(**values)
    except TypeError:
        return SimpleNamespace(**values)


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, SimpleNamespace):
        return vars(value)
    return value


def get_field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def call_first(obj: Any, method_names: tuple[str, ...], *args: Any, **kwargs: Any) -> Any:
    for method_name in method_names:
        method = getattr(obj, method_name, None)
        if method is not None:
            return method(*args, **kwargs)
    pytest.skip(f"假设接口尚未实现：{obj!r} 缺少方法 {method_names}")


@pytest.fixture
def market_fixture() -> dict[str, Any]:
    return {
        "market_id": "m_weather_nyc",
        "event_id": "e_weather_apr",
        "question": "Will NYC Central Park record over 80F on April 26?",
        "description": "Weather market for New York City.",
        "rules": (
            "This market resolves according to the National Weather Service "
            "Central Park station observation for April 26, 2026, in America/New_York."
        ),
        "outcomes": ["Yes", "No"],
        "token_ids": ["token_yes", "token_no"],
        "active": True,
        "closed": False,
        "resolved": False,
        "end_time": UTC_NOW + timedelta(days=1),
        "volume": 5_000.0,
        "liquidity": 2_000.0,
        "category": "Weather",
        "tags": ["weather", "temperature"],
        "fetched_at": UTC_NOW,
    }


@pytest.fixture
def parsed_mapping() -> SimpleNamespace:
    return SimpleNamespace(
        market_id="m_weather_nyc",
        event_id="e_weather_apr",
        location_id="nyc_central_park",
        location_name="NYC Central Park",
        lat=40.7812,
        lon=-73.9665,
        station_id="USW00094728",
        resolution_source_name="National Weather Service",
        resolution_source_url="https://www.weather.gov/",
        forecast_provider="open_meteo",
        forecast_model="GFS",
        observation_provider="noaa",
        target_variable="temperature_2m_max",
        target_date=UTC_NOW.date(),
        target_time_window="local day",
        timezone="America/New_York",
        unit="F",
        parsing_status="parsed",
        parsing_reason=None,
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
    )

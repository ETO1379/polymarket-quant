from __future__ import annotations

import pytest

from conftest import get_field, import_attr, make_model, optional_attr


class FailingAccountProvider:
    def get_snapshot(self):
        AuthenticationError = optional_attr("data_ingestion.core.errors", "AuthenticationError") or RuntimeError
        raise AuthenticationError("account auth failed")


class EmptyProvider:
    def __getattr__(self, _name):
        def _empty(*_args, **_kwargs):
            return []

        return _empty


def test_runner_disables_live_trading_when_account_provider_missing():
    IngestionRunner = import_attr("data_ingestion.services.ingestion_runner", "IngestionRunner")
    IngestionConfig = optional_attr("data_ingestion.config.schemas", "IngestionConfig")

    config = make_model(
        IngestionConfig,
        dry_run=False,
        live_trading_allowed=True,
        data_ingestion={},
    )

    package = IngestionRunner(
        config=config,
        market_provider=EmptyProvider(),
        price_provider=EmptyProvider(),
        weather_provider=EmptyProvider(),
        account_provider=None,
        storage_writer=EmptyProvider(),
        monitoring_sink=EmptyProvider(),
    ).run_once()

    run_context = get_field(package, "run_context")
    assert get_field(run_context, "live_trading_allowed") is False
    assert get_field(run_context, "dry_run") is True
    assert "dry" in str(get_field(run_context, "mode", "")).lower()
    assert get_field(package, "errors", [])


def test_runner_disables_live_trading_when_account_read_fails():
    IngestionRunner = import_attr("data_ingestion.services.ingestion_runner", "IngestionRunner")
    IngestionConfig = optional_attr("data_ingestion.config.schemas", "IngestionConfig")

    config = make_model(
        IngestionConfig,
        dry_run=False,
        live_trading_allowed=True,
        data_ingestion={},
    )

    try:
        runner = IngestionRunner(
            config=config,
            market_provider=EmptyProvider(),
            price_provider=EmptyProvider(),
            weather_provider=EmptyProvider(),
            account_provider=FailingAccountProvider(),
            storage_writer=EmptyProvider(),
            monitoring_sink=EmptyProvider(),
        )
    except TypeError:
        runner = IngestionRunner(config=config, account_provider=FailingAccountProvider())

    package = runner.run_once()

    run_context = get_field(package, "run_context")
    assert get_field(run_context, "live_trading_allowed") is False
    assert get_field(run_context, "dry_run") is True or "observation" in str(get_field(run_context, "mode", ""))

    errors = get_field(package, "errors", [])
    assert errors
    assert any("auth" in str(error).lower() or "account" in str(error).lower() for error in errors)

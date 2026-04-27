from __future__ import annotations

from pathlib import Path

from conftest import import_attr


def test_loader_resolves_wallet_env_placeholder(monkeypatch):
    load_ingestion_config = import_attr("data_ingestion.config.loader", "load_ingestion_config")
    monkeypatch.setenv("POLYMARKET_WALLET_ADDRESS", "0xabc")
    path = Path(".pytest_cache/test_data_ingestion_env.toml")
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
[data_ingestion]
dry_run = true

[data_ingestion.account]
wallet_address = "${POLYMARKET_WALLET_ADDRESS}"
api_key_ref = "POLYMARKET_API_KEY"
""",
        encoding="utf-8",
    )

    config = load_ingestion_config(path)

    assert config.account.wallet_address == "0xabc"


def test_loader_does_not_keep_unresolved_wallet_placeholder(monkeypatch):
    load_ingestion_config = import_attr("data_ingestion.config.loader", "load_ingestion_config")
    monkeypatch.delenv("POLYMARKET_WALLET_ADDRESS", raising=False)
    path = Path(".pytest_cache/test_data_ingestion_missing_env.toml")
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
[data_ingestion.account]
wallet_address = "${POLYMARKET_WALLET_ADDRESS}"
""",
        encoding="utf-8",
    )

    config = load_ingestion_config(path)

    assert config.account.wallet_address is None

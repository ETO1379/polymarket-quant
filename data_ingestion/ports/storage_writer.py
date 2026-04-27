from __future__ import annotations

from typing import Protocol

from data_ingestion.core.package import RawDataPackage
from data_ingestion.core.models import PriceHistoryRaw


class StorageWriter(Protocol):
    def save_raw_package(self, package: RawDataPackage) -> None:
        ...

    def save_price_history(self, rows: list[PriceHistoryRaw]) -> None:
        ...


class NoopStorageWriter:
    def save_raw_package(self, package: RawDataPackage) -> None:
        return None

    def save_price_history(self, rows: list[PriceHistoryRaw]) -> None:
        return None

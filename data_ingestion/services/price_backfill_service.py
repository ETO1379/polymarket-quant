from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from data_ingestion.core.models import PriceHistoryRaw


@dataclass(slots=True)
class BackfillRequest:
    market_id: str | None
    token_id: str | None
    start_time: datetime | None
    end_time: datetime | None
    fidelity: str
    use_max_range: bool = False
    interval: str | None = None
    fidelity_minutes: int | None = None


class PriceHistoryProvider(Protocol):
    def get_price_history(self, request: BackfillRequest) -> list[PriceHistoryRaw]:
        ...


class PriceBackfillService:
    def __init__(
        self,
        provider: PriceHistoryProvider | None = None,
        *,
        max_backfill_days: int = 30,
        allow_max_range: bool = False,
    ) -> None:
        self.provider = provider
        self.max_backfill_days = max_backfill_days
        self.allow_max_range = allow_max_range

    def validate_request(self, request: BackfillRequest) -> BackfillRequest:
        if not getattr(request, "token_id", None):
            raise ValueError("token_id is required for price history backfill")
        interval = getattr(request, "interval", None)
        start_time = getattr(request, "start_time", None)
        end_time = getattr(request, "end_time", None)
        if interval and (start_time or end_time):
            raise ValueError("interval is mutually exclusive with start_time/end_time")
        if getattr(request, "use_max_range", False) or getattr(request, "fidelity", None) == "max" or interval == "max":
            if not self.allow_max_range:
                raise ValueError("max range backfill is disabled by configuration")
        if start_time and end_time and end_time < start_time:
            raise ValueError("end_time must be after start_time")
        if start_time and end_time and (end_time - start_time).total_seconds() > self.max_backfill_days * 86400:
            raise ValueError("backfill range exceeds max_backfill_days")
        return request

    def backfill(self, request: BackfillRequest) -> list[PriceHistoryRaw]:
        self.validate_request(request)
        if self.provider is None:
            return []
        rows = self.provider.get_price_history(request)
        self._validate_rows(rows)
        return rows

    def _validate_rows(self, rows: list[PriceHistoryRaw]) -> None:
        seen: set[tuple[str, datetime, str]] = set()
        for row in rows:
            key = (row.token_id, row.timestamp, row.fidelity)
            if key in seen:
                raise ValueError("duplicated price history point")
            seen.add(key)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FreshnessResult:
    data_type: str
    market_id: str | None
    source_timestamp: datetime | None
    fetched_at: datetime
    max_age_seconds: int
    is_stale: bool
    reason: str


class FreshnessCheck:
    def check(
        self,
        *,
        data_type: str,
        market_id: str | None = None,
        source_timestamp: datetime | None,
        fetched_at: datetime,
        max_age_seconds: int,
    ) -> FreshnessResult:
        if source_timestamp is None:
            return FreshnessResult(
                data_type=data_type,
                market_id=market_id,
                source_timestamp=source_timestamp,
                fetched_at=fetched_at,
                max_age_seconds=max_age_seconds,
                is_stale=True,
                reason="source timestamp missing; data is stale",
            )
        age_seconds = (fetched_at - source_timestamp).total_seconds()
        is_stale = age_seconds > max_age_seconds
        reason = "stale: source timestamp exceeds max age" if is_stale else "fresh"
        return FreshnessResult(
            data_type=data_type,
            market_id=market_id,
            source_timestamp=source_timestamp,
            fetched_at=fetched_at,
            max_age_seconds=max_age_seconds,
            is_stale=is_stale,
            reason=reason,
        )

    def evaluate(self, **kwargs) -> FreshnessResult:
        return self.check(**kwargs)

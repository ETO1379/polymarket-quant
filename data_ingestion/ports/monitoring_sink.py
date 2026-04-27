from __future__ import annotations

from typing import Protocol

from data_ingestion.core.errors import IngestionErrorRecord
from data_ingestion.core.models import IngestionMetrics


class MonitoringSink(Protocol):
    def emit_metrics(self, metrics: IngestionMetrics) -> None:
        ...

    def emit_error(self, error: IngestionErrorRecord) -> None:
        ...


class NoopMonitoringSink:
    def emit_metrics(self, metrics: IngestionMetrics) -> None:
        return None

    def emit_error(self, error: IngestionErrorRecord) -> None:
        return None

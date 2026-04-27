from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from data_ingestion.core.time import utc_now


class IngestionError(Exception):
    error_type = "IngestionError"


class AuthenticationError(IngestionError):
    error_type = "AuthenticationError"


class PermissionError(IngestionError):
    error_type = "PermissionError"


class RateLimitError(IngestionError):
    error_type = "RateLimitError"


class NetworkError(IngestionError):
    error_type = "NetworkError"


class TimeoutError(IngestionError):
    error_type = "TimeoutError"


class SchemaChangedError(IngestionError):
    error_type = "SchemaChangedError"


class EmptyDataError(IngestionError):
    error_type = "EmptyDataError"


class DataStaleError(IngestionError):
    error_type = "DataStaleError"


class PartialDataError(IngestionError):
    error_type = "PartialDataError"


@dataclass(slots=True)
class IngestionErrorRecord:
    error_type: str
    message: str
    provider: str | None = None
    endpoint: str | None = None
    request_id: str | None = None
    market_id: str | None = None
    token_id: str | None = None
    occurred_at: datetime = field(default_factory=utc_now)
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        *,
        provider: str | None = None,
        endpoint: str | None = None,
        request_id: str | None = None,
        market_id: str | None = None,
        token_id: str | None = None,
    ) -> "IngestionErrorRecord":
        return cls(
            error_type=getattr(exc, "error_type", exc.__class__.__name__),
            message=str(exc),
            provider=provider,
            endpoint=endpoint,
            request_id=request_id,
            market_id=market_id,
            token_id=token_id,
        )

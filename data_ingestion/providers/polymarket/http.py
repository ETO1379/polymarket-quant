from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from data_ingestion.core.errors import (
    AuthenticationError,
    NetworkError,
    PermissionError,
    RateLimitError,
    SchemaChangedError,
    TimeoutError as IngestionTimeoutError,
)


@dataclass(slots=True)
class HttpJsonClient:
    base_url: str
    timeout_seconds: float = 10
    retry_times: int = 3
    rate_limit_per_second: float | None = None
    user_agent: str = "polymarket-quant-data-ingestion/0.1"

    def get_json(self, path: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        if self.rate_limit_per_second:
            time.sleep(1 / self.rate_limit_per_second)
        query = f"?{urlencode(params or {}, doseq=True)}" if params else ""
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}{query}"
        request = Request(url, headers={"User-Agent": self.user_agent, **(headers or {})})
        last_exc: Exception | None = None
        for attempt in range(max(1, self.retry_times)):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw)
            except HTTPError as exc:
                if exc.code in {401, 403}:
                    if exc.code == 401:
                        raise AuthenticationError("authentication failed") from exc
                    raise PermissionError("permission denied") from exc
                if exc.code == 429:
                    last_exc = RateLimitError("rate limited")
                elif exc.code >= 500:
                    last_exc = NetworkError(f"server error {exc.code}")
                else:
                    raise SchemaChangedError(f"unexpected http status {exc.code}") from exc
            except (TimeoutError, socket.timeout) as exc:
                last_exc = IngestionTimeoutError("request timed out")
            except URLError as exc:
                last_exc = NetworkError(str(exc))
            if attempt < self.retry_times - 1:
                time.sleep(0.2 * (2**attempt))
        if last_exc:
            raise last_exc
        raise NetworkError("request failed")

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import unquote

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=10.0)


class BaseAsyncService:
    """Shared async HTTP client with retry and context-manager support."""

    def __init__(self, *, timeout: httpx.Timeout | float = _DEFAULT_TIMEOUT):
        self._client = httpx.AsyncClient(http2=True, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _get_json(self, url: str, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        safe_params = None
        if params is not None:
            safe_params = {
                k: (unquote(v) if isinstance(v, str) and "%" in v else v)
                for k, v in params.items()
            }

        resp = await self._client.get(url, params=safe_params, headers=headers)
        resp.raise_for_status()
        return resp.json()

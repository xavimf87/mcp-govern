"""Client HTTP centralitzat amb retries, rate limiting i User-Agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "mcp-govern/0.1.0 (dades obertes; +https://github.com/xavimf87/mcp-govern)"
DEFAULT_TIMEOUT = 30.0

# Max concurrent requests per domain
MAX_CONCURRENT_PER_DOMAIN = 5

# Retry config
MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
BACKOFF_BASE = 1.0  # seconds

# Per-domain semaphores
_domain_semaphores: dict[str, asyncio.Semaphore] = {}


def _get_semaphore(url: str) -> asyncio.Semaphore:
    """Obté o crea un semàfor per al domini de la URL."""
    domain = urlparse(url).netloc
    if domain not in _domain_semaphores:
        _domain_semaphores[domain] = asyncio.Semaphore(MAX_CONCURRENT_PER_DOMAIN)
    return _domain_semaphores[domain]


def create_client(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    follow_redirects: bool = False,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    """Crea un client HTTP configurat amb User-Agent i timeout."""
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        headers=h,
    )


async def fetch_json(
    url: str,
    *,
    params: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    follow_redirects: bool = False,
    max_retries: int = MAX_RETRIES,
) -> Any:
    """GET amb retries, rate limiting i parse JSON.

    Reinitenta automàticament en cas de:
    - HTTP 429 (Too Many Requests)
    - HTTP 5xx (errors de servidor)
    - Errors de connexió transitoris
    """
    sem = _get_semaphore(url)
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)

    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        async with sem:
            try:
                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=follow_redirects,
                    headers=h,
                ) as client:
                    resp = await client.get(url, params=params)

                    if resp.status_code in RETRY_STATUS_CODES and attempt < max_retries:
                        # Respectar Retry-After si existeix
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after:
                            try:
                                wait = float(retry_after)
                            except ValueError:
                                wait = BACKOFF_BASE * (2**attempt)
                        else:
                            wait = BACKOFF_BASE * (2**attempt)
                        logger.warning(
                            "HTTP %d de %s — reintentant en %.1fs (intent %d/%d)",
                            resp.status_code,
                            urlparse(url).netloc,
                            wait,
                            attempt + 1,
                            max_retries,
                        )
                        await asyncio.sleep(wait)
                        continue

                    resp.raise_for_status()
                    return resp.json()

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout) as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "%s de %s — reintentant en %.1fs (intent %d/%d)",
                        type(exc).__name__,
                        urlparse(url).netloc,
                        wait,
                        attempt + 1,
                        max_retries,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise

    # Should not reach here, but just in case
    if last_exc:
        raise last_exc
    raise httpx.HTTPError("Max retries exceeded")

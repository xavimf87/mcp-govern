"""Client async per a la SODA API (Socrata) de dades obertes de Catalunya."""

from __future__ import annotations

import httpx

from .datasets import dataset_url

DEFAULT_LIMIT = 20
MAX_LIMIT = 50_000
REQUEST_TIMEOUT = 60.0


async def query(
    dataset_key: str,
    *,
    select: str | None = None,
    where: str | None = None,
    q: str | None = None,
    order: str | None = None,
    group: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> list[dict]:
    """Executa una consulta SoQL contra un dataset de Socrata."""
    params: dict[str, str] = {}

    if select:
        params["$select"] = select
    if where:
        params["$where"] = where
    if q:
        params["$q"] = q
    if order:
        params["$order"] = order
    if group:
        params["$group"] = group

    params["$limit"] = str(min(limit, MAX_LIMIT))
    if offset > 0:
        params["$offset"] = str(offset)

    url = dataset_url(dataset_key)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

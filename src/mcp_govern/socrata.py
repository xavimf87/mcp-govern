"""Client async per a la SODA API (Socrata) de dades obertes de Catalunya."""

from __future__ import annotations

import asyncio

import httpx

from . import http
from .datasets import DATASETS, dataset_url

METADATA_BASE = "https://analisi.transparenciacatalunya.cat/api/views"
DEFAULT_LIMIT = 50
MAX_LIMIT = 50_000
REQUEST_TIMEOUT = 60.0


async def _count(
    client: httpx.AsyncClient,
    url: str,
    *,
    where: str | None = None,
    q: str | None = None,
) -> int | None:
    """Fa un COUNT(*) per saber el total de resultats disponibles."""
    params: dict[str, str] = {"$select": "count(*)"}
    if where:
        params["$where"] = where
    if q:
        params["$q"] = q
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return int(data[0].get("count", 0))
    except httpx.HTTPError:
        pass
    return None


async def discover_camps(dataset_key: str) -> list[str]:
    """Descobreix els camps d'un dataset via l'API de metadades de Socrata.

    Consulta /api/views/{id}.json per obtenir les columnes reals del dataset.
    Útil com a fallback quan el dataset no té camps definits estàticament.
    """
    info = DATASETS.get(dataset_key)
    if not info:
        return []
    dataset_id = info["id"]
    url = f"{METADATA_BASE}/{dataset_id}.json"
    data = await http.fetch_json(url, timeout=REQUEST_TIMEOUT)
    columns = data.get("columns", [])
    return [col["fieldName"] for col in columns if col.get("fieldName") and not col["fieldName"].startswith(":")]


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

    return await http.fetch_json(url, params=params, timeout=REQUEST_TIMEOUT)


async def query_with_count(
    dataset_key: str,
    *,
    select: str | None = None,
    where: str | None = None,
    q: str | None = None,
    order: str | None = None,
    group: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> tuple[list[dict], int | None]:
    """Com query() però retorna també el total de resultats disponibles.

    Retorna (records, total). total pot ser None si el count falla.
    Si és un GROUP BY, no fa count (no tindria sentit).
    """
    url = dataset_url(dataset_key)

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

    async with http.create_client(timeout=REQUEST_TIMEOUT) as client:
        if group:
            # Per a GROUP BY no té sentit fer count
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json(), None

        # Llançar query + count en paral·lel
        query_task = client.get(url, params=params)
        count_task = _count(client, url, where=where, q=q)

        resp, total = await asyncio.gather(query_task, count_task)
        resp.raise_for_status()
        return resp.json(), total

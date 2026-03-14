"""Client async per a la API de datos.gob.es (catàleg nacional de dades obertes)."""

from __future__ import annotations

import httpx

BASE_URL = "https://datos.gob.es/apidata"
REQUEST_TIMEOUT = 30.0
DEFAULT_PAGE_SIZE = 20


async def buscar_datasets(
    *,
    query: str | None = None,
    theme: str | None = None,
    publisher: str | None = None,
    format_: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    page: int = 0,
) -> dict:
    """Cerca datasets al catàleg nacional de dades obertes.

    Args:
        query: Text lliure per cercar als títols i descripcions.
        theme: Temàtica (ex: 'sector-publico', 'economia', 'hacienda').
        publisher: Organisme publicador.
        format_: Format dels recursos (ex: 'json', 'csv', 'api').
        page_size: Resultats per pàgina.
        page: Número de pàgina (0-indexed).
    """
    params: dict[str, str | int] = {
        "_pageSize": page_size,
        "_page": page,
        "_sort": "-modified",
    }
    if query:
        params["q"] = query
    if theme:
        params["theme_id"] = f"http://datos.gob.es/kos/sector-publico/sector/{theme}"
    if publisher:
        params["publisher_display_name"] = publisher
    if format_:
        params["format"] = format_

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/catalog/dataset.json", params=params)
        resp.raise_for_status()
        return resp.json()


async def detall_dataset(dataset_id: str) -> dict:
    """Obté el detall complet d'un dataset pel seu identificador.

    Args:
        dataset_id: Identificador del dataset (ex: 'l01080193-presupuestos-gastos').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/catalog/dataset/{dataset_id}.json"
        )
        resp.raise_for_status()
        return resp.json()


async def buscar_distribucions(
    *,
    dataset_id: str | None = None,
    format_: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    page: int = 0,
) -> dict:
    """Cerca distribucions (fitxers/APIs) de datasets.

    Args:
        dataset_id: Filtrar per dataset concret.
        format_: Format del recurs (ex: 'text/csv', 'application/json').
        page_size: Resultats per pàgina.
        page: Número de pàgina.
    """
    params: dict[str, str | int] = {
        "_pageSize": page_size,
        "_page": page,
    }
    if format_:
        params["format"] = format_

    url = f"{BASE_URL}/catalog/distribution.json"
    if dataset_id:
        url = f"{BASE_URL}/catalog/dataset/{dataset_id}/distribution.json"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

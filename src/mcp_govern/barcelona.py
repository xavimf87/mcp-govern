"""Client async per a l'Open Data de l'Ajuntament de Barcelona (API CKAN)."""

from __future__ import annotations

import httpx

BASE_URL = "https://opendata-ajuntament.barcelona.cat/data/api/action"
REQUEST_TIMEOUT = 30.0
DEFAULT_ROWS = 20

# Datasets destacats per àrea temàtica
BARCELONA_DATASETS = {
    # Pressupostos
    "pressupost_despeses": "pressupost-despeses",
    "pressupost_ingressos": "pressupost-ingressos",
    # Contractació
    "contractes_menors": "contractes-menors",
    "modificacions_contractes": "modificacions-de-contractes",
    "prorrogues_contractes": "prorrogues-de-contractes",
    "relacio_contractistes": "relacio-contractistes",
    # Seguretat
    "incidents_gub": "incidents-gestionats-gub",
    "denuncies_transit": "denuncies_sancions_transit_bcn_detall",
    # Transport
    "transports": "transports",
    "bicing": "bicing",
    "carril_bici": "carril-bici",
    "aparcaments": "aparcaments-bcn",
    # Medi ambient
    "qualitat_aire": "qualitat-aire-detall-bcn",
    "espais_verds": "espais-verds-publics",
    # Habitatge
    "habitatges_2na_ma": "habitatges-2na-ma",
    "habitatges_turistic": "habitatges-us-turistic",
    # Economia
    "renda_llars": "renda-disponible-llars-bcn",
    # Urbanisme
    "obres": "obres",
}


async def cercar_datasets(
    *,
    query: str | None = None,
    rows: int = DEFAULT_ROWS,
    start: int = 0,
) -> dict:
    """Cerca datasets a l'Open Data de Barcelona.

    Args:
        query: Text lliure per cercar.
        rows: Nombre de resultats.
        start: Offset per paginació.
    """
    params: dict[str, str | int] = {
        "rows": rows,
        "start": start,
    }
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/package_search", params=params)
        resp.raise_for_status()
        return resp.json()


async def detall_dataset(dataset_name: str) -> dict:
    """Obté el detall complet d'un dataset pel seu nom.

    Args:
        dataset_name: Nom del dataset (ex: 'pressupost-despeses').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/package_show",
            params={"id": dataset_name},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_dades(
    resource_id: str,
    *,
    query: str | None = None,
    filters: dict | None = None,
    limit: int = DEFAULT_ROWS,
    offset: int = 0,
) -> dict:
    """Obté dades d'un recurs concret via l'API datastore.

    Args:
        resource_id: ID del recurs (obtingut via detall_dataset).
        query: Text lliure per filtrar.
        filters: Diccionari de filtres exactes (camp: valor).
        limit: Nombre de resultats.
        offset: Offset per paginació.
    """
    params: dict[str, str | int] = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset,
    }
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/datastore_search",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

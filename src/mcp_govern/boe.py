"""Client async per a l'API de dades obertes del BOE (Boletín Oficial del Estado)."""

from __future__ import annotations

from . import http

BASE_URL = "https://www.boe.es/datosabiertos/api"
REQUEST_TIMEOUT = 30.0

_ACCEPT_JSON = {"Accept": "application/json"}


async def obtenir_sumari(data: str) -> dict:
    """Obté el sumari del BOE per una data concreta.

    Args:
        data: Data en format YYYYMMDD (ex: '20260314').
    """
    return await http.fetch_json(
        f"{BASE_URL}/boe/sumario/{data}",
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )


async def cercar_legislacio(
    *,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Cerca legislació consolidada.

    L'API del BOE no suporta filtres, només paginació.
    El filtrat per títol/departament/rang es fa al servidor MCP.

    Args:
        limit: Nombre de resultats.
        offset: Offset per paginació.
    """
    return await http.fetch_json(
        f"{BASE_URL}/legislacion-consolidada",
        params={"limit": limit, "offset": offset},
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )


async def obtenir_departaments() -> dict:
    """Obté la llista de departaments del BOE."""
    return await http.fetch_json(
        f"{BASE_URL}/datos-auxiliares/departamentos",
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )


async def obtenir_rangs() -> dict:
    """Obté la llista de rangs normatius del BOE."""
    return await http.fetch_json(
        f"{BASE_URL}/datos-auxiliares/rangos",
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )


async def obtenir_materies() -> dict:
    """Obté la llista de matèries del BOE."""
    return await http.fetch_json(
        f"{BASE_URL}/datos-auxiliares/materias",
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )


async def obtenir_sumari_borme(data: str) -> dict:
    """Obté el sumari del BORME per una data concreta.

    Args:
        data: Data en format YYYYMMDD (ex: '20260314').
    """
    return await http.fetch_json(
        f"{BASE_URL}/borme/sumario/{data}",
        headers=_ACCEPT_JSON,
        timeout=REQUEST_TIMEOUT,
    )

"""Client async per a l'API de dades obertes del BOE (Boletín Oficial del Estado)."""

from __future__ import annotations

import httpx

BASE_URL = "https://www.boe.es/datosabiertos/api"
REQUEST_TIMEOUT = 30.0


async def obtenir_sumari(data: str) -> dict:
    """Obté el sumari del BOE per una data concreta.

    Args:
        data: Data en format YYYYMMDD (ex: '20260314').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/boe/sumario/{data}",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def cercar_legislacio(
    *,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Cerca legislació consolidada.

    Args:
        limit: Nombre de resultats.
        offset: Offset per paginació.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/legislacion-consolidada",
            params={"limit": limit, "offset": offset},
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_departaments() -> dict:
    """Obté la llista de departaments del BOE."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/datos-auxiliares/departamentos",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_rangs() -> dict:
    """Obté la llista de rangs normatius del BOE."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/datos-auxiliares/rangos",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_materies() -> dict:
    """Obté la llista de matèries del BOE."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/datos-auxiliares/materias",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_sumari_borme(data: str) -> dict:
    """Obté el sumari del BORME per una data concreta.

    Args:
        data: Data en format YYYYMMDD (ex: '20260314').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/borme/sumario/{data}",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

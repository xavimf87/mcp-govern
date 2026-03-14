"""Client async per a l'API de l'INE (Instituto Nacional de Estadística)."""

from __future__ import annotations

import httpx

BASE_URL = "https://servicios.ine.es/wstempus/js/ES"
REQUEST_TIMEOUT = 30.0


async def llistar_operacions() -> list:
    """Llista totes les operacions estadístiques disponibles."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/OPERACIONES_DISPONIBLES")
        resp.raise_for_status()
        return resp.json()


async def llistar_taules(operacio: str) -> list:
    """Llista les taules d'una operació estadística.

    Args:
        operacio: Codi de l'operació (ex: 'IPC', 'EPA', 'ECV').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/TABLAS_OPERACION/{operacio}")
        resp.raise_for_status()
        return resp.json()


async def obtenir_dades_taula(taula_id: int, *, nult: int = 5) -> list:
    """Obté les dades d'una taula estadística.

    Args:
        taula_id: ID numèric de la taula.
        nult: Nombre d'últims períodes a retornar (per defecte 5).
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/DATOS_TABLA/{taula_id}",
            params={"nult": nult},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_serie(serie: str, *, nult: int = 10) -> list:
    """Obté una sèrie temporal concreta.

    Args:
        serie: Codi de la sèrie (ex: 'IPC206449').
        nult: Nombre d'últims períodes a retornar.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/DATOS_SERIE/{serie}",
            params={"nult": nult},
        )
        resp.raise_for_status()
        return resp.json()

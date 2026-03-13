"""Client async per a la API del BDNS (Base de Datos Nacional de Subvenciones)."""

from __future__ import annotations

import httpx

BASE_URL = "https://www.pap.hacienda.gob.es/bdnstrans"
API_URL = f"{BASE_URL}/api"
REQUEST_TIMEOUT = 30.0
DEFAULT_PAGE_SIZE = 50


async def buscar_concessions(
    *,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    page: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """Cerca concessions via la API REST (filtre per dates).

    Args:
        fecha_desde: Data inici DD/MM/YYYY
        fecha_hasta: Data fi DD/MM/YYYY
        page: Pàgina (0-indexed)
        page_size: Resultats per pàgina
    """
    params: dict[str, str] = {
        "vpd": "GE",
        "page": str(page),
        "pageSize": str(page_size),
    }
    if fecha_desde:
        params["fechaDesde"] = fecha_desde
    if fecha_hasta:
        params["fechaHasta"] = fecha_hasta

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{API_URL}/concesiones/busqueda", params=params)
        resp.raise_for_status()
        return resp.json()


async def buscar_convocatories(
    *,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    page: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """Cerca convocatòries via la API REST."""
    params: dict[str, str] = {
        "vpd": "GE",
        "page": str(page),
        "pageSize": str(page_size),
    }
    if fecha_desde:
        params["fechaDesde"] = fecha_desde
    if fecha_hasta:
        params["fechaHasta"] = fecha_hasta

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{API_URL}/convocatorias/busqueda", params=params)
        resp.raise_for_status()
        return resp.json()


async def detall_convocatoria(num_conv: str) -> dict:
    """Obté el detall complet d'una convocatòria pel seu número BDNS."""
    params = {"numConv": num_conv, "vpd": "GE"}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{API_URL}/convocatorias", params=params)
        resp.raise_for_status()
        return resp.json()

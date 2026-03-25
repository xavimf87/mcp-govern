"""Client async per a la API del BDNS (Base de Datos Nacional de Subvenciones)."""

from __future__ import annotations

from . import http

BASE_URL = "https://www.pap.hacienda.gob.es/bdnstrans"
API_URL = f"{BASE_URL}/api"
REQUEST_TIMEOUT = 30.0
DEFAULT_PAGE_SIZE = 50


async def buscar_concessions(
    *,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    texto: str | None = None,
    organo: str | None = None,
    comunidad: str | None = None,
    page: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """Cerca concessions via la API REST (filtre per dates, text, òrgan, comunitat).

    Args:
        fecha_desde: Data inici DD/MM/YYYY
        fecha_hasta: Data fi DD/MM/YYYY
        texto: Text lliure per cercar (beneficiari, convocatòria...)
        organo: Òrgan convocant
        comunidad: Comunitat autònoma (ex: 'CATALUÑA', 'MADRID')
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
    if texto:
        params["texto"] = texto
    if organo:
        params["organo"] = organo
    if comunidad:
        params["comunidadAutonoma"] = comunidad

    return await http.fetch_json(f"{API_URL}/concesiones/busqueda", params=params, timeout=REQUEST_TIMEOUT)


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

    return await http.fetch_json(f"{API_URL}/convocatorias/busqueda", params=params, timeout=REQUEST_TIMEOUT)


async def detall_convocatoria(num_conv: str) -> dict:
    """Obté el detall complet d'una convocatòria pel seu número BDNS."""
    params = {"numConv": num_conv, "vpd": "GE"}
    return await http.fetch_json(f"{API_URL}/convocatorias", params=params, timeout=REQUEST_TIMEOUT)

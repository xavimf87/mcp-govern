"""Client async per a l'API de l'INE (Instituto Nacional de Estadística)."""

from __future__ import annotations

from . import http

BASE_URL = "https://servicios.ine.es/wstempus/js/ES"
REQUEST_TIMEOUT = 30.0


async def llistar_operacions() -> list:
    """Llista totes les operacions estadístiques disponibles."""
    return await http.fetch_json(f"{BASE_URL}/OPERACIONES_DISPONIBLES", timeout=REQUEST_TIMEOUT)


async def llistar_taules(operacio: str) -> list:
    """Llista les taules d'una operació estadística.

    Args:
        operacio: Codi de l'operació (ex: 'IPC', 'EPA', 'ECV').
    """
    return await http.fetch_json(f"{BASE_URL}/TABLAS_OPERACION/{operacio}", timeout=REQUEST_TIMEOUT)


async def obtenir_dades_taula(taula_id: int, *, nult: int = 5) -> list:
    """Obté les dades d'una taula estadística.

    Args:
        taula_id: ID numèric de la taula.
        nult: Nombre d'últims períodes a retornar (per defecte 5).
    """
    return await http.fetch_json(
        f"{BASE_URL}/DATOS_TABLA/{taula_id}",
        params={"nult": nult},
        timeout=REQUEST_TIMEOUT,
    )


async def obtenir_serie(serie: str, *, nult: int = 10) -> list:
    """Obté una sèrie temporal concreta.

    Args:
        serie: Codi de la sèrie (ex: 'IPC206449').
        nult: Nombre d'últims períodes a retornar.
    """
    return await http.fetch_json(
        f"{BASE_URL}/DATOS_SERIE/{serie}",
        params={"nult": nult},
        timeout=REQUEST_TIMEOUT,
    )

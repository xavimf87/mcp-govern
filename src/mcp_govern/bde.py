"""Client async per a l'API del Banc d'Espanya (BdE)."""

from __future__ import annotations

import httpx

BASE_URL = "https://app.bde.es/bierest/resources/srdatosapp"
REQUEST_TIMEOUT = 30.0

# Sèries destacades
SERIES_DESTACADES = {
    "euribor_1any": "D_1NBAF472",
    "euribor_3mesos": "D_1NBAF474",
    "euribor_6mesos": "D_1NBAF473",
    "euribor_12mesos": "D_1NBAF472",
    "ipc_general": "D_1AEA8S1",
    "deute_public_espanya": "D_1BE9994",
    "tipus_interes_bce": "D_1NBAF468",
}


async def obtenir_ultim_valor(series: str) -> list:
    """Obté l'últim valor disponible de les sèries indicades.

    Args:
        series: Codis de sèries separats per comes (ex: 'D_1NBAF472').
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/favoritas",
            params={"idioma": "es", "series": series},
            headers={"Accept-Encoding": "gzip"},
        )
        resp.raise_for_status()
        return resp.json()


async def obtenir_metadades_serie(series: str, *, rang: str = "MAX") -> list:
    """Obté metadades d'una sèrie (descripció, font, freqüència).

    Args:
        series: Codis de sèries separats per comes.
        rang: Rang temporal: '30M', '60M', 'MAX', o un any com '2024'.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            f"{BASE_URL}/listaSeries",
            params={"idioma": "es", "series": series, "rango": rang},
            headers={"Accept-Encoding": "gzip"},
        )
        resp.raise_for_status()
        return resp.json()

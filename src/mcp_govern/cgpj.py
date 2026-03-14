"""Client async per a dades del CGPJ (Consejo General del Poder Judicial).

Accedeix a les estadístiques judicials i al repositori de processos
per corrupció publicats pel CGPJ via la seva API de dades obertes.
"""

from __future__ import annotations

import httpx

# API pública d'estadística judicial del CGPJ
BASE_URL = "https://www.poderjudicial.es"
STATS_API = f"{BASE_URL}/cgpj/es/Temas/Estadistica-Judicial/Estadistica-por-Temas"
REQUEST_TIMEOUT = 30.0

# URL del repositori de dades sobre processos per corrupció
CORRUPCION_URL = (
    f"{BASE_URL}/cgpj/es/Temas/Transparencia/Repositorio-de-datos-sobre"
    "-procesos-por-corrupcion/"
)

# Endpoint PC-Axis per estadístiques judicials
PCAXIS_API = f"{BASE_URL}/stj/pcaxis"


async def buscar_estadistiques_judicials(
    *,
    tema: str | None = None,
    territori: str | None = None,
    any_: str | None = None,
) -> dict:
    """Cerca estadístiques judicials al CGPJ.

    Args:
        tema: Tema de l'estadística (ex: 'penal', 'civil', 'contencioso').
        territori: Àmbit territorial (ex: 'nacional', 'Madrid', 'Barcelona').
        any_: Any de les estadístiques.
    """
    params: dict[str, str] = {}
    if tema:
        params["tema"] = tema
    if territori:
        params["territorio"] = territori
    if any_:
        params["anio"] = any_

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(f"{PCAXIS_API}/juzgados.json", params=params)
        resp.raise_for_status()
        return resp.json()


async def obtenir_dades_corrupcio() -> dict:
    """Obté les dades del repositori de processos per corrupció del CGPJ.

    Retorna informació sobre procediments judicials per corrupció
    incloent: macrocauses, causes a Audiència Nacional i tribunals
    superiors de justícia.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        # Intentar obtenir dades via la API JSON
        resp = await client.get(
            f"{PCAXIS_API}/corrupcion.json",
        )
        if resp.status_code == 200:
            return resp.json()

        # Fallback: obtenir la pàgina HTML del repositori
        resp = await client.get(CORRUPCION_URL)
        resp.raise_for_status()
        return {
            "font": CORRUPCION_URL,
            "nota": (
                "Les dades de corrupció del CGPJ es publiquen com a informes "
                "PDF i taules estadístiques. Consulta la URL font per accedir "
                "als documents complets."
            ),
            "url_repositori": CORRUPCION_URL,
            "status": resp.status_code,
        }


async def cercar_sentencies(
    *,
    text: str | None = None,
    organ: str | None = None,
    tipus: str | None = None,
    data_desde: str | None = None,
    data_fins: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Cerca sentències al Centre de Documentació Judicial (CENDOJ).

    Args:
        text: Text lliure per cercar a les resolucions.
        organ: Tipus d'òrgan judicial (ex: 'TS' Tribunal Suprem,
               'AN' Audiència Nacional, 'AP' Audiència Provincial).
        tipus: Tipus de resolució (ex: 'SENTENCIA', 'AUTO').
        data_desde: Data inici DD/MM/YYYY.
        data_fins: Data fi DD/MM/YYYY.
        page: Pàgina de resultats.
        page_size: Resultats per pàgina.
    """
    params: dict[str, str | int] = {
        "page": page,
        "pageSize": page_size,
    }
    if text:
        params["q"] = text
    if organ:
        params["organ"] = organ
    if tipus:
        params["tipo"] = tipus
    if data_desde:
        params["fechaDesde"] = data_desde
    if data_fins:
        params["fechaHasta"] = data_fins

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(
            f"{BASE_URL}/search/indexAN",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

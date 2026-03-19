"""Client async per a dades del CGPJ (Consejo General del Poder Judicial).

Accedeix al repositori de processos per corrupció publicat pel CGPJ.

NOTA: Les APIs públiques d'estadística judicial (stj/pcaxis) i el
cercador de sentències (CENDOJ /search/indexAN) van ser desactivades
pel CGPJ (retornen 404/403). Només resta disponible el repositori
HTML de corrupció.
"""

from __future__ import annotations

import httpx

BASE_URL = "https://www.poderjudicial.es"
REQUEST_TIMEOUT = 30.0

# URL del repositori de dades sobre processos per corrupció
CORRUPCION_URL = (
    f"{BASE_URL}/cgpj/es/Temas/Transparencia/Repositorio-de-datos-sobre"
    "-procesos-por-corrupcion/"
)


async def buscar_estadistiques_judicials(
    *,
    tema: str | None = None,
    territori: str | None = None,
    any_: str | None = None,
) -> dict:
    """Cerca estadístiques judicials al CGPJ.

    NOTA: L'API pública d'estadística judicial (stj/pcaxis) ha estat
    desactivada pel CGPJ i retorna 404. Es retorna un missatge informatiu
    amb l'URL del portal web on es poden consultar manualment.
    """
    return {
        "error": "API no disponible",
        "nota": (
            "L'API pública d'estadística judicial del CGPJ "
            "(stj/pcaxis/juzgados.json) ha estat desactivada i retorna 404. "
            "Les estadístiques es poden consultar manualment al portal web."
        ),
        "url_portal": (
            f"{BASE_URL}/cgpj/es/Temas/Estadistica-Judicial/"
            "Estadistica-por-Temas"
        ),
    }


async def obtenir_dades_corrupcio() -> dict:
    """Obté les dades del repositori de processos per corrupció del CGPJ.

    Retorna informació sobre procediments judicials per corrupció
    incloent: macrocauses, causes a Audiència Nacional i tribunals
    superiors de justícia.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
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

    NOTA: L'API del CENDOJ (/search/indexAN) ha estat restringida pel
    CGPJ i retorna 403 Forbidden. Es retorna un missatge informatiu.
    """
    return {
        "error": "API no disponible",
        "nota": (
            "L'API del cercador de sentències del CENDOJ "
            "(/search/indexAN) ha estat restringida pel CGPJ i "
            "retorna 403 Forbidden. Les sentències es poden consultar "
            "manualment al portal web."
        ),
        "url_portal": f"{BASE_URL}/search/indexAN",
    }

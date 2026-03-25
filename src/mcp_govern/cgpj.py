"""Client async per a dades del CGPJ (Consejo General del Poder Judicial).

Accedeix a:
- Repositori de processos per corrupció (HTML)
- Cercador de sentències del CENDOJ (scraping amb User-Agent de navegador)
- Estadístiques judicials via PxWeb (www6.poderjudicial.es)
"""

from __future__ import annotations

import re
from html import unescape

from . import http

BASE_URL = "https://www.poderjudicial.es"
PXWEB_BASE = "https://www6.poderjudicial.es/PxWeb-20252-v1/pxweb"
REQUEST_TIMEOUT = 30.0

# El CENDOJ bloqueja peticions sense User-Agent de navegador
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# URL del repositori de dades sobre processos per corrupció
CORRUPCION_URL = f"{BASE_URL}/cgpj/es/Temas/Transparencia/Repositorio-de-datos-sobre-procesos-por-corrupcion/"

# El CENDOJ actualment només permet cercar a l'Audiència Nacional (AN).
# Altres codis (TS, AP, TSJ, JPI) retornen 404.
_CENDOJ_DB = "AN"


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
    """Cerca sentències al CENDOJ via scraping del cercador web.

    El CENDOJ requereix User-Agent de navegador (retorna 403 altrament).
    Parseja l'HTML de resultats per extreure sentències.
    """
    if not text:
        return {
            "error": "Cal especificar un text de cerca",
            "nota": "El cercador del CENDOJ requereix almenys un terme de cerca.",
        }

    # El CENDOJ només permet cercar a l'Audiència Nacional (AN)
    search_url = f"{BASE_URL}/search/sentencias/{text}/{page}/{_CENDOJ_DB}"

    async with http.create_client(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": _BROWSER_UA},
    ) as client:
        resp = await client.get(search_url)
        resp.raise_for_status()
        html = resp.text

    sentencies = _parse_sentencies_html(html, text)

    return {
        "resultats": sentencies,
        "total_mostrats": len(sentencies),
        "pagina": page,
        "base_dades": _CENDOJ_DB,
        "url_cerca": search_url,
        "nota": (
            "Resultats obtinguts del CENDOJ (Audiència Nacional). "
            "Per veure el text complet d'una sentència, usa la URL proporcionada. "
            "Nota: el CENDOJ actualment només permet cerques a l'Audiència Nacional."
        ),
    }


def _fmt_date(yyyymmdd: str) -> str:
    """Converteix YYYYMMDD a DD/MM/YYYY."""
    if len(yyyymmdd) == 8:
        return f"{yyyymmdd[6:8]}/{yyyymmdd[4:6]}/{yyyymmdd[:4]}"
    return yyyymmdd


def _parse_sentencies_html(html: str, query: str) -> list[dict]:
    """Extreu sentències de l'HTML de resultats del CENDOJ.

    Usa dos estratègies:
    1. Links /search/documento/{organ}/{id}/{query}/{date} per obtenir documents
    2. data-roj attributes per obtenir ROJ i ECLI
    """
    results = []
    seen_ids: set[str] = set()

    # Estratègia principal: extreure links de documents (sempre presents)
    doc_pattern = re.compile(
        r'/search/documento/(\w+)/(\d+)/[^/"]*/(\d+)',
    )
    for match in doc_pattern.finditer(html):
        organ = match.group(1)
        doc_id = match.group(2)
        fecha = match.group(3)
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        entry: dict[str, str] = {
            "id": doc_id,
            "organ": organ,
            "data": _fmt_date(fecha),
            "url": f"{BASE_URL}/search/documento/{organ}/{doc_id}/{query}/{fecha}",
        }

        # Buscar ROJ i ECLI associats a aquest document (data-roj proper)
        roj_match = re.search(
            rf'data-reference="{doc_id}"[^>]*data-roj="([^"]+)"',
            html,
        )
        if roj_match:
            entry["roj"] = roj_match.group(1)
        ecli_match = re.search(
            rf'id="{doc_id}".*?ECLI:[A-Z0-9:]+',
            html,
            re.DOTALL,
        )
        if ecli_match:
            ecli = re.search(r"ECLI:[A-Z0-9:]+", ecli_match.group(0))
            if ecli:
                entry["ecli"] = ecli.group(0)

        results.append(entry)

    # Si no trobem res, comprovar si no hi ha resultats
    if not results and re.search(r"no se han encontrado|sin resultados|0 resultados", html, re.IGNORECASE):
        return []

    return results


def _clean_html(text: str) -> str:
    """Elimina tags HTML i neteja espais."""
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def obtenir_dades_corrupcio() -> dict:
    """Obté les dades del repositori de processos per corrupció del CGPJ."""
    async with http.create_client(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    ) as client:
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


async def buscar_estadistiques_judicials(
    *,
    tema: str | None = None,
    territori: str | None = None,
    any_: str | None = None,
) -> dict:
    """Cerca estadístiques judicials al portal PxWeb del CGPJ.

    Llista les bases de dades disponibles i, si s'especifica un tema,
    intenta obtenir les taules corresponents.
    """
    async with http.create_client(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": _BROWSER_UA},
    ) as client:
        # Obtenir la llista de bases de dades disponibles
        menu_url = f"{PXWEB_BASE}/es/"
        resp = await client.get(menu_url)
        resp.raise_for_status()
        html = resp.text

    # Parsejar les bases de dades disponibles
    databases = _parse_pxweb_menu(html)

    if not databases:
        return {
            "error": "No s'han pogut obtenir les bases de dades del CGPJ",
            "url_portal": f"{PXWEB_BASE}/es/",
            "nota": "Consulta el portal PxWeb directament.",
        }

    # Si s'ha especificat un tema, filtrar
    if tema:
        tema_lower = tema.lower()
        filtered = [db for db in databases if tema_lower in db.get("nom", "").lower()]
        if filtered:
            databases = filtered

    return {
        "bases_dades": databases,
        "total": len(databases),
        "url_portal": f"{PXWEB_BASE}/es/",
        "nota": (
            "L'API REST del PxWeb del CGPJ no és funcional. "
            "Es mostren les bases de dades disponibles al portal web. "
            "Cada base de dades conté taules amb estadístiques judicials "
            "des de 1995 fins a l'actualitat."
        ),
    }


def _parse_pxweb_menu(html: str) -> list[dict]:
    """Extreu les bases de dades del menú PxWeb."""
    results = []
    # El menú PxWeb té enllaços amb format: /PxWeb-.../pxweb/es/NN.-Nom/
    pattern = re.compile(
        r'<a[^>]*href="([^"]*pxweb/es/[^"]*)"[^>]*>\s*(.*?)\s*</a>',
        re.IGNORECASE | re.DOTALL,
    )
    seen = set()
    for match in pattern.finditer(html):
        href = match.group(1)
        nom = _clean_html(match.group(2))
        if not nom or nom in seen or len(nom) < 3:
            continue
        # Filtrar només entrades de bases de dades (tenen número al davant)
        if re.match(r"\d+\.", nom):
            seen.add(nom)
            results.append(
                {
                    "nom": nom,
                    "url": href if href.startswith("http") else f"https://www6.poderjudicial.es{href}",
                }
            )
    return results

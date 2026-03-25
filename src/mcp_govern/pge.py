"""Client async per als Pressupostos Generals de l'Estat (PGE)."""

from __future__ import annotations

import csv
import io
from xml.etree import ElementTree

import httpx

from . import http

BASE_URL = "https://www.hacienda.gob.es/sgt/gobiernoabierto/datos%20abiertos"
REQUEST_TIMEOUT = 30.0

# Anys disponibles amb PGE aprovats o prorrogats (verificats a l'API).
# 2020-2022 no tenen fitxers XML publicats (pressupostos prorrogats sense dades obertes).
# 2025 pendent de verificar quan es publiquin.
ANYS_DISPONIBLES = [2019, 2023, 2024]


def _url_index(any_: int) -> str:
    """Construeix la URL de l'índex XML per un any."""
    return f"{BASE_URL}/pge_transparencia/infoportaltransppresupuesto-l{any_}-p.xml"


async def obtenir_index(any_: int) -> dict:
    """Obté l'índex XML dels pressupostos d'un any.

    Args:
        any_: Any dels pressupostos (ex: 2024).

    Returns:
        Dict amb l'estructura de l'índex (seccions, apartats, enllaços).
    """
    async with http.create_client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(_url_index(any_))
        resp.raise_for_status()

        # El XML pot venir amb encoding ISO-8859-1
        content = resp.content
        root = ElementTree.fromstring(content)
        return _parse_element(root)


def _parse_element(element: ElementTree.Element) -> dict:
    """Parseja recursivament un element XML a dict."""
    result: dict = {}
    if element.text and element.text.strip():
        result["text"] = element.text.strip()
    if element.attrib:
        result.update(element.attrib)

    children: dict[str, list] = {}
    for child in element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        parsed = _parse_element(child)
        children.setdefault(tag, []).append(parsed)

    for tag, items in children.items():
        if len(items) == 1:
            result[tag] = items[0]
        else:
            result[tag] = items

    return result


async def descarregar_csv(url: str) -> str:
    """Descarrega un fitxer CSV de pressupostos.

    Args:
        url: URL completa del CSV (obtinguda via obtenir_index).
    """
    async with http.create_client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def obtenir_despeses(any_: int, seccio: str | None = None) -> list[dict]:
    """Obté les despeses dels PGE per un any concret.

    Descarrega i parseja els CSV de despeses per programa.
    """
    index = await obtenir_index(any_)

    # Navigate the XML structure to find CSV links for spending data
    estructura = index.get("Estructura", {})
    sector = estructura.get("Estructura", {})
    seccions_raw = sector.get("Estructura", [])
    if isinstance(seccions_raw, dict):
        seccions_raw = [seccions_raw]

    csv_urls = []
    for sec in seccions_raw:
        sec_code = sec.get("codigo", "")
        sec_name = sec.get("literal", "")
        if seccio and seccio.lower() not in sec_name.lower() and seccio != sec_code:
            continue
        subsectors = sec.get("Estructura", [])
        if isinstance(subsectors, dict):
            subsectors = [subsectors]
        for sub in subsectors:
            informe = sub.get("Informe", {})
            if isinstance(informe, dict):
                enlaces = informe.get("Enlace", [])
                if isinstance(enlaces, dict):
                    enlaces = [enlaces]
                for enllac in enlaces:
                    url = enllac.get("url", "")
                    if url and (url.endswith(".CSV") or url.endswith(".csv")):
                        csv_urls.append(
                            {
                                "seccio": sec_code,
                                "nom_seccio": sec_name,
                                "url": url,
                            }
                        )

    if not csv_urls:
        return []

    # Download first CSV to show data structure
    # Limit to first 5 CSVs to avoid timeout
    results = []
    async with http.create_client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for info in csv_urls[:5]:
            try:
                resp = await client.get(info["url"])
                resp.raise_for_status()
                text = resp.text
                reader = csv.DictReader(io.StringIO(text), delimiter=";")
                rows = []
                for i, row in enumerate(reader):
                    if i >= 20:  # Max 20 rows per CSV
                        break
                    row["_seccio"] = info["nom_seccio"]
                    rows.append(row)
                results.extend(rows)
            except (httpx.HTTPError, Exception):
                continue

    return results

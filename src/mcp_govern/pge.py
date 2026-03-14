"""Client async per als Pressupostos Generals de l'Estat (PGE)."""

from __future__ import annotations

from xml.etree import ElementTree

import httpx

BASE_URL = "https://www.hacienda.gob.es/sgt/gobiernoabierto/datos%20abiertos"
REQUEST_TIMEOUT = 30.0

# Anys disponibles amb PGE aprovats o prorrogats
ANYS_DISPONIBLES = list(range(2015, 2026))


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
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
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
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

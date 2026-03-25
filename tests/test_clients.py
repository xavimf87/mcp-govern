"""Tests per als mòduls client (boe, bdns, ine, bde, barcelona, datosgob, pge)."""

from __future__ import annotations

import pytest
import respx

from mcp_govern import barcelona, bde, bdns, boe, datosgob, ine, pge

# ===========================================================================
# BOE
# ===========================================================================


class TestBoe:
    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_sumari(self):
        respx.get(f"{boe.BASE_URL}/boe/sumario/20260314").respond(
            json={"status": {"code": "200"}, "data": []},
        )
        result = await boe.obtenir_sumari("20260314")
        assert result["status"]["code"] == "200"

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_sumari_borme(self):
        respx.get(f"{boe.BASE_URL}/borme/sumario/20260314").respond(
            json={"status": {"code": "200"}},
        )
        result = await boe.obtenir_sumari_borme("20260314")
        assert result["status"]["code"] == "200"

    @pytest.mark.asyncio
    @respx.mock
    async def test_cercar_legislacio(self):
        respx.get(f"{boe.BASE_URL}/legislacion-consolidada").respond(
            json={"status": {"code": "200"}, "data": []},
        )
        result = await boe.cercar_legislacio()
        assert result["status"]["code"] == "200"

    @pytest.mark.asyncio
    @respx.mock
    async def test_cercar_legislacio_pagination(self):
        route = respx.get(f"{boe.BASE_URL}/legislacion-consolidada").respond(
            json={"status": {"code": "200"}, "data": []},
        )
        await boe.cercar_legislacio(limit=5, offset=10)
        url_str = str(route.calls[0].request.url)
        assert "limit=5" in url_str
        assert "offset=10" in url_str

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_departaments(self):
        respx.get(f"{boe.BASE_URL}/datos-auxiliares/departamentos").respond(
            json={"status": {"code": "200"}, "data": [{"nombre": "Interior"}]},
        )
        result = await boe.obtenir_departaments()
        assert result["data"][0]["nombre"] == "Interior"


# ===========================================================================
# BDNS
# ===========================================================================


class TestBdns:
    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_concessions(self):
        respx.get(f"{bdns.API_URL}/concesiones/busqueda").respond(
            json={"content": [], "totalElements": 0},
        )
        result = await bdns.buscar_concessions()
        assert "content" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_concessions_with_texto(self):
        route = respx.get(f"{bdns.API_URL}/concesiones/busqueda").respond(
            json={"content": [{"beneficiario": "Test"}], "totalElements": 1},
        )
        result = await bdns.buscar_concessions(texto="Test")
        assert result["totalElements"] == 1
        assert "texto=Test" in str(route.calls[0].request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_concessions_with_comunidad(self):
        route = respx.get(f"{bdns.API_URL}/concesiones/busqueda").respond(
            json={"content": [], "totalElements": 0},
        )
        await bdns.buscar_concessions(comunidad="CATALUÑA")
        assert "comunidadAutonoma" in str(route.calls[0].request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_convocatories(self):
        respx.get(f"{bdns.API_URL}/convocatorias/busqueda").respond(
            json={"content": [], "totalElements": 0},
        )
        result = await bdns.buscar_convocatories()
        assert "content" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_detall_convocatoria(self):
        respx.get(f"{bdns.API_URL}/convocatorias").respond(
            json={"numConv": "12345", "titulo": "Test"},
        )
        result = await bdns.detall_convocatoria("12345")
        assert result["numConv"] == "12345"


# ===========================================================================
# INE
# ===========================================================================


class TestIne:
    @pytest.mark.asyncio
    @respx.mock
    async def test_llistar_operacions(self):
        respx.get(f"{ine.BASE_URL}/OPERACIONES_DISPONIBLES").respond(
            json=[{"Id": 25, "Nombre": "IPC"}],
        )
        result = await ine.llistar_operacions()
        assert len(result) == 1
        assert result[0]["Nombre"] == "IPC"

    @pytest.mark.asyncio
    @respx.mock
    async def test_llistar_taules(self):
        respx.get(f"{ine.BASE_URL}/TABLAS_OPERACION/IPC").respond(
            json=[{"Id": 100, "Nombre": "Taula IPC"}],
        )
        result = await ine.llistar_taules("IPC")
        assert result[0]["Nombre"] == "Taula IPC"

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_dades_taula(self):
        respx.get(f"{ine.BASE_URL}/DATOS_TABLA/100").respond(
            json=[{"Nombre": "IPC General", "Data": []}],
        )
        result = await ine.obtenir_dades_taula(100)
        assert result[0]["Nombre"] == "IPC General"

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_serie(self):
        respx.get(f"{ine.BASE_URL}/DATOS_SERIE/IPC206449").respond(
            json=[{"Valor": 105.3}],
        )
        result = await ine.obtenir_serie("IPC206449")
        assert result[0]["Valor"] == 105.3


# ===========================================================================
# BdE (Banc d'Espanya)
# ===========================================================================


class TestBde:
    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_ultim_valor(self):
        respx.get(f"{bde.BASE_URL}/favoritas").respond(
            json=[{"serie": "D_1NBAF472", "valor": "3.5"}],
        )
        result = await bde.obtenir_ultim_valor("D_1NBAF472")
        assert result[0]["valor"] == "3.5"

    def test_series_destacades(self):
        assert "euribor_1any" in bde.SERIES_DESTACADES
        assert "deute_public_espanya" in bde.SERIES_DESTACADES
        assert len(bde.SERIES_DESTACADES) >= 5

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_metadades_serie(self):
        respx.get(f"{bde.BASE_URL}/listaSeries").respond(
            json=[{"serie": "D_1NBAF472", "descripcion": "Euribor 1 any"}],
        )
        result = await bde.obtenir_metadades_serie("D_1NBAF472")
        assert result[0]["descripcion"] == "Euribor 1 any"


# ===========================================================================
# Barcelona Open Data
# ===========================================================================


class TestBarcelona:
    @pytest.mark.asyncio
    @respx.mock
    async def test_cercar_datasets(self):
        respx.get(f"{barcelona.BASE_URL}/package_search").respond(
            json={"success": True, "result": {"results": [{"name": "test"}]}},
        )
        result = await barcelona.cercar_datasets()
        assert result["success"] is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_detall_dataset(self):
        respx.get(f"{barcelona.BASE_URL}/package_show").respond(
            json={"success": True, "result": {"name": "test", "resources": []}},
        )
        result = await barcelona.detall_dataset("test")
        assert result["result"]["name"] == "test"

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_dades(self):
        respx.get(f"{barcelona.BASE_URL}/datastore_search").respond(
            json={"success": True, "result": {"records": [{"a": 1}]}},
        )
        result = await barcelona.obtenir_dades("resource-123")
        assert result["result"]["records"][0]["a"] == 1

    def test_barcelona_datasets_map(self):
        assert "pressupost_despeses" in barcelona.BARCELONA_DATASETS
        assert "incidents_gub" in barcelona.BARCELONA_DATASETS
        assert len(barcelona.BARCELONA_DATASETS) >= 15


# ===========================================================================
# datos.gob.es
# ===========================================================================


class TestDatosGob:
    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_datasets(self):
        respx.get(f"{datosgob.BASE_URL}/catalog/dataset.json").respond(
            json={"result": {"items": []}},
        )
        result = await datosgob.buscar_datasets()
        assert "result" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_buscar_datasets_with_query(self):
        respx.get(f"{datosgob.BASE_URL}/catalog/dataset/keyword/presupuestos.json").respond(
            json={"result": {"items": [{"title": "Presupuestos"}]}},
        )
        result = await datosgob.buscar_datasets(query="presupuestos")
        assert "result" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_detall_dataset(self):
        respx.get(f"{datosgob.BASE_URL}/catalog/dataset/test-id.json").respond(
            json={"result": {"title": "Test"}},
        )
        result = await datosgob.detall_dataset("test-id")
        assert result["result"]["title"] == "Test"


# ===========================================================================
# PGE
# ===========================================================================


class TestPge:
    def test_anys_disponibles(self):
        assert len(pge.ANYS_DISPONIBLES) >= 3
        assert 2024 in pge.ANYS_DISPONIBLES

    def test_url_index(self):
        url = pge._url_index(2024)
        assert "2024" in url
        assert url.endswith(".xml")

    @pytest.mark.asyncio
    @respx.mock
    async def test_obtenir_index(self):
        xml = """<?xml version="1.0"?>
        <root>
            <seccion nombre="Gastos">
                <apartado nombre="Estado"/>
            </seccion>
        </root>"""
        respx.get(pge._url_index(2024)).respond(
            status_code=200,
            content=xml.encode(),
            headers={"Content-Type": "application/xml"},
        )
        result = await pge.obtenir_index(2024)
        assert "seccion" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_descarregar_csv(self):
        csv_data = "col1,col2\nval1,val2\n"
        respx.get("https://example.com/test.csv").respond(
            status_code=200,
            text=csv_data,
        )
        result = await pge.descarregar_csv("https://example.com/test.csv")
        assert "col1" in result
        assert "val1" in result

    def test_parse_element(self):
        from xml.etree import ElementTree

        xml = "<root><child attr='val'>text</child></root>"
        root = ElementTree.fromstring(xml)
        result = pge._parse_element(root)
        assert "child" in result
        assert result["child"]["text"] == "text"
        assert result["child"]["attr"] == "val"

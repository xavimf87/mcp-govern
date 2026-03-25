"""Smoke tests contra APIs reals.

Cada test fa UNA crida per font de dades per verificar connectivitat
i format de resposta. No son tests exhaustius, sino canaris que detecten
si una API ha canviat el seu schema o URL.

Executar manualment: uv run pytest tests/integration/ -v
"""

from __future__ import annotations

import pytest

from mcp_govern import barcelona, bde, bdns, boe, cgpj, datosgob, ine, socrata

pytestmark = pytest.mark.asyncio


class TestSocrata:
    async def test_contractes_query(self):
        records = await socrata.query("contractes", limit=1)
        assert isinstance(records, list)
        assert len(records) <= 1
        if records:
            assert "exercici" in records[0] or "adjudicatari" in records[0]

    async def test_count(self):
        records, total = await socrata.query_with_count("contractes", limit=1)
        assert isinstance(records, list)
        assert total is None or total > 0


class TestBdns:
    async def test_concessions(self):
        result = await bdns.buscar_concessions(page_size=1)
        assert "content" in result
        assert "totalElements" in result

    async def test_convocatories(self):
        result = await bdns.buscar_convocatories(page_size=1)
        assert "content" in result


class TestBoe:
    async def test_departaments(self):
        result = await boe.obtenir_departaments()
        assert result.get("status", {}).get("code") == "200"

    async def test_legislacio(self):
        result = await boe.cercar_legislacio(limit=1)
        assert result.get("status", {}).get("code") == "200"


class TestIne:
    async def test_operacions(self):
        ops = await ine.llistar_operacions()
        assert isinstance(ops, list)
        assert len(ops) > 50


class TestBde:
    async def test_series_destacades(self):
        result = await bde.obtenir_ultim_valor(bde.SERIES_DESTACADES["euribor_1any"])
        assert isinstance(result, list)
        assert len(result) >= 1


class TestDatosGob:
    async def test_buscar_datasets(self):
        result = await datosgob.buscar_datasets(page_size=1)
        assert "result" in result


class TestBarcelona:
    async def test_cercar_datasets(self):
        result = await barcelona.cercar_datasets(rows=1)
        assert result.get("success") is True


class TestCgpj:
    async def test_estadistiques(self):
        result = await cgpj.buscar_estadistiques_judicials()
        assert "bases_dades" in result or "error" in result

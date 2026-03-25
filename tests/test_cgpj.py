"""Tests per al mòdul cgpj.py (CGPJ client)."""

from __future__ import annotations

import pytest
import respx

from mcp_govern import cgpj


class TestCercarSentencies:
    @pytest.mark.asyncio
    async def test_requires_text(self):
        result = await cgpj.cercar_sentencies()
        assert result["error"] == "Cal especificar un text de cerca"

    @pytest.mark.asyncio
    @respx.mock
    async def test_parses_documents(self):
        html = """
        <html>
        <div class="searchresult doc" id="12345">
            <a data-link="/search/documento/AN/12345/test/20260101"
               data-reference="12345" data-roj="SAN 100/2026"
               data-databasematch="AN" data-links="test" data-fechares="20260101"
               href="/search/documento/AN/12345/test/20260101">
               ROJ: SAN 100/2026 - ECLI:ES:AN:2026:100
            </a>
        </div>
        </html>
        """
        respx.get(f"{cgpj.BASE_URL}/search/sentencias/test/1/AN").respond(
            status_code=200,
            text=html,
        )
        result = await cgpj.cercar_sentencies(text="test")
        assert result["total_mostrats"] >= 1
        assert result["resultats"][0]["id"] == "12345"
        assert result["resultats"][0]["organ"] == "AN"
        assert result["resultats"][0]["data"] == "01/01/2026"

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_results(self):
        html = "<html><body>no se han encontrado resultados</body></html>"
        respx.get(f"{cgpj.BASE_URL}/search/sentencias/xyz/1/AN").respond(
            status_code=200,
            text=html,
        )
        result = await cgpj.cercar_sentencies(text="xyz")
        assert result["total_mostrats"] == 0
        assert result["resultats"] == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_pagination(self):
        html = '<html><a href="/search/documento/AN/99/q/20260301">doc</a></html>'
        respx.get(f"{cgpj.BASE_URL}/search/sentencias/q/3/AN").respond(
            status_code=200,
            text=html,
        )
        result = await cgpj.cercar_sentencies(text="q", page=3)
        assert result["pagina"] == 3


class TestEstadistiquesJudicials:
    @pytest.mark.asyncio
    @respx.mock
    async def test_lists_databases(self):
        html = """
        <html>
        <a href="/PxWeb-20252-v1/pxweb/es/01.-Tribunal%20Supremo/">01.-Tribunal Supremo</a>
        <a href="/PxWeb-20252-v1/pxweb/es/02.-Audiencia%20Nacional/">02.-Audiencia Nacional</a>
        </html>
        """
        respx.get(f"{cgpj.PXWEB_BASE}/es/").respond(status_code=200, text=html)
        result = await cgpj.buscar_estadistiques_judicials()
        assert result["total"] == 2
        assert "Tribunal Supremo" in result["bases_dades"][0]["nom"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_filter_by_tema(self):
        html = """
        <html>
        <a href="/PxWeb-20252-v1/pxweb/es/01.-Tribunal%20Supremo/">01.-Tribunal Supremo</a>
        <a href="/PxWeb-20252-v1/pxweb/es/07.-Juzgados%20de%20lo%20Penal/">07.-Juzgados de lo Penal</a>
        </html>
        """
        respx.get(f"{cgpj.PXWEB_BASE}/es/").respond(status_code=200, text=html)
        result = await cgpj.buscar_estadistiques_judicials(tema="penal")
        assert result["total"] == 1
        assert "Penal" in result["bases_dades"][0]["nom"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_empty_page(self):
        respx.get(f"{cgpj.PXWEB_BASE}/es/").respond(status_code=200, text="<html></html>")
        result = await cgpj.buscar_estadistiques_judicials()
        assert "error" in result


class TestDadesCorrupcio:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_info(self):
        respx.get(cgpj.CORRUPCION_URL).respond(status_code=200, text="<html>data</html>")
        result = await cgpj.obtenir_dades_corrupcio()
        assert result["status"] == 200
        assert "url_repositori" in result


class TestFmtDate:
    def test_valid_date(self):
        assert cgpj._fmt_date("20260315") == "15/03/2026"

    def test_short_date(self):
        assert cgpj._fmt_date("2026") == "2026"

    def test_empty(self):
        assert cgpj._fmt_date("") == ""


class TestCleanHtml:
    def test_removes_tags(self):
        assert cgpj._clean_html("<b>bold</b>") == "bold"

    def test_unescapes(self):
        assert cgpj._clean_html("a&amp;b") == "a&b"

    def test_normalizes_spaces(self):
        assert cgpj._clean_html("a   b\n\tc") == "a b c"

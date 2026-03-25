"""Tests per al mòdul socrata.py (SODA API client)."""

from __future__ import annotations

import httpx
import pytest
import respx

from mcp_govern import socrata
from mcp_govern.datasets import DATASETS

# ---------------------------------------------------------------------------
# discover_camps
# ---------------------------------------------------------------------------


class TestDiscoverCamps:
    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_camps_returns_field_names(self):
        dataset_id = DATASETS["contractes"]["id"]
        url = f"{socrata.METADATA_BASE}/{dataset_id}.json"
        respx.get(url).respond(
            json={
                "columns": [
                    {
                        "fieldName": "exercici",
                        "name": "Exercici",
                        "dataTypeName": "text",
                    },
                    {
                        "fieldName": "adjudicatari",
                        "name": "Adjudicatari",
                        "dataTypeName": "text",
                    },
                    {"fieldName": ":id", "name": "ID intern", "dataTypeName": "text"},
                ]
            }
        )
        camps = await socrata.discover_camps("contractes")
        assert camps == ["exercici", "adjudicatari"]
        assert ":id" not in camps

    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_camps_unknown_dataset(self):
        camps = await socrata.discover_camps("dataset_inexistent")
        assert camps == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_discover_camps_empty_columns(self):
        dataset_id = DATASETS["contractes"]["id"]
        url = f"{socrata.METADATA_BASE}/{dataset_id}.json"
        respx.get(url).respond(json={"columns": []})
        camps = await socrata.discover_camps("contractes")
        assert camps == []


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


class TestQuery:
    @pytest.mark.asyncio
    @respx.mock
    async def test_query_basic(self):
        from mcp_govern.datasets import dataset_url

        url = dataset_url("contractes")
        respx.get(url).respond(json=[{"exercici": "2024"}])
        result = await socrata.query("contractes")
        assert result == [{"exercici": "2024"}]

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_with_params(self):
        from mcp_govern.datasets import dataset_url

        url = dataset_url("contractes")
        respx.get(url).respond(json=[])
        result = await socrata.query(
            "contractes",
            where="exercici='2024'",
            limit=10,
            offset=5,
        )
        assert result == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_query_http_error(self):
        from mcp_govern.datasets import dataset_url

        url = dataset_url("contractes")
        respx.get(url).respond(status_code=500)
        with pytest.raises(httpx.HTTPStatusError):
            await socrata.query("contractes")


# ---------------------------------------------------------------------------
# _count
# ---------------------------------------------------------------------------


class TestCount:
    @pytest.mark.asyncio
    @respx.mock
    async def test_count_success(self):
        url = "https://example.com/test.json"
        respx.get(url).respond(json=[{"count": "42"}])
        async with httpx.AsyncClient() as client:
            result = await socrata._count(client, url)
        assert result == 42

    @pytest.mark.asyncio
    @respx.mock
    async def test_count_http_error_returns_none(self):
        url = "https://example.com/test.json"
        respx.get(url).respond(status_code=500)
        async with httpx.AsyncClient() as client:
            result = await socrata._count(client, url)
        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_count_empty_response(self):
        url = "https://example.com/test.json"
        respx.get(url).respond(json=[])
        async with httpx.AsyncClient() as client:
            result = await socrata._count(client, url)
        assert result is None


# ---------------------------------------------------------------------------
# query_with_count
# ---------------------------------------------------------------------------


class TestQueryWithCount:
    @pytest.mark.asyncio
    @respx.mock
    async def test_query_with_count_group_by(self):
        from mcp_govern.datasets import dataset_url

        url = dataset_url("contractes")
        respx.get(url).respond(json=[{"exercici": "2024", "count": "5"}])
        records, total = await socrata.query_with_count(
            "contractes",
            select="exercici, count(*)",
            group="exercici",
        )
        assert records == [{"exercici": "2024", "count": "5"}]
        assert total is None

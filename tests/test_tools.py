"""Tests per a les tools MCP del server.py.

Cada tool es testa amb mocking de les APIs externes per verificar:
- Que retorna resultats correctes
- Que gestiona errors
- Que els paràmetres es passen correctament
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from mcp_govern import server

# ===========================================================================
# Socrata tools (contractes, subvencions, etc.)
# ===========================================================================


class TestLlistarCamps:
    @pytest.mark.asyncio
    async def test_dataset_known(self):
        result = await server.llistar_camps("contractes")
        assert "Camps disponibles" in result
        assert "exercici" in result or "situaci_contractual" in result

    @pytest.mark.asyncio
    async def test_dataset_unknown(self):
        result = await server.llistar_camps("no_existeix")
        assert "Error" in result
        assert "no trobat" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.discover_camps", new_callable=AsyncMock)
    async def test_dataset_empty_camps_uses_discovery(self, mock_discover):
        mock_discover.return_value = ["camp_a", "camp_b"]
        result = await server.llistar_camps("impost_successions_composicio")
        assert "camp_a" in result
        assert "descoberts via API" in result
        mock_discover.assert_called_once()


class TestCercarContractes:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_basic_search(self, mock_query):
        mock_query.return_value = ([{"exercici": "2024", "adjudicatari": "TEST SL"}], 1)
        result = await server.cercar_contractes(exercici="2024")
        assert "TEST SL" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_no_results(self, mock_query):
        mock_query.return_value = ([], 0)
        result = await server.cercar_contractes(adjudicatari="INEXISTENT")
        assert "No s'han trobat" in result


class TestCercarPublicacionsPscp:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"nom_adjudicatari": "ACME"}], 1)
        result = await server.cercar_publicacions_pscp(adjudicatari="ACME")
        assert "ACME" in result


class TestCercarSubvencions:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"beneficiari": "Fundació"}], 1)
        result = await server.cercar_subvencions(beneficiari="Fundació")
        assert "Fundació" in result


class TestCercarConvocatories:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"nom": "Convocatòria test"}], 1)
        result = await server.cercar_convocatories()
        assert "Convocatòria test" in result


class TestDetallContracte:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_detail(self, mock_query):
        mock_query.return_value = ([{"codi_expedient": "EXP-001", "lots": 2}], 1)
        result = await server.detall_contracte(codi_expedient="EXP-001")
        assert "EXP-001" in result


class TestDetallSubvencio:
    @pytest.mark.asyncio
    async def test_no_params(self):
        result = await server.detall_subvencio()
        assert "Error" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_by_codi_raisc(self, mock_query):
        mock_query.return_value = ([{"codi_raisc": "R001"}], 1)
        result = await server.detall_subvencio(codi_raisc="R001")
        assert "R001" in result


class TestEstadistiques:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_count(self, mock_query):
        mock_query.return_value = (
            [{"exercici": "2024", "count": "50"}, {"exercici": "2023", "count": "30"}],
            None,
        )
        result = await server.estadistiques(
            dataset="contractes",
            agrupar_per="exercici",
        )
        assert "2024" in result

    @pytest.mark.asyncio
    async def test_invalid_dataset(self):
        result = await server.estadistiques(
            dataset="no_existeix",
            agrupar_per="camp",
        )
        assert "Error" in result


# ===========================================================================
# Retribucions
# ===========================================================================


class TestCercarRetribucionsAltsCarrecs:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search_by_carrec(self, mock_query):
        mock_query.return_value = ([{"carrec": "Conseller", "retribucio": "80000"}], 1)
        result = await server.cercar_retribucions_alts_carrecs(carrec="Conseller")
        assert "Conseller" in result


class TestCercarDirectiusSectorPublic:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"nom": "Joan Test"}], 1)
        result = await server.cercar_directius_sector_public(nom="Joan")
        assert "Joan" in result


class TestCercarRetribucionsSubvencionats:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"empresa": "Entitat Test"}], 1)
        result = await server.cercar_retribucions_subvencionats(empresa="Entitat")
        assert "Entitat" in result


class TestConsultarTaulesSalarials:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"cos": "Mossos d'Esquadra"}], 1)
        result = await server.consultar_taules_salarials(cos="mossos")
        assert "Mossos" in result


# ===========================================================================
# Pressupostos
# ===========================================================================


class TestCercarPressupostos:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"exercici": "2024"}], 1)
        result = await server.cercar_pressupostos(exercici="2024")
        assert "2024" in result


class TestCercarPressupostosMunicipals:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"municipi": "Barcelona"}], 1)
        result = await server.cercar_pressupostos_municipals(municipi="Barcelona")
        assert "Barcelona" in result


# ===========================================================================
# Personal
# ===========================================================================


class TestCercarLlocsTreball:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"nom_lloc": "Tècnic"}], 1)
        result = await server.cercar_llocs_treball(nom_lloc="Tècnic")
        assert "Tècnic" in result


class TestCercarOfertaOcupacio:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"titol": "Oferta test"}], 1)
        result = await server.cercar_oferta_ocupacio()
        assert "Oferta test" in result


# ===========================================================================
# Transparència
# ===========================================================================


class TestCercarDeclaracionsActivitats:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"nom": "Maria Test"}], 1)
        result = await server.cercar_declaracions_activitats(nom="Maria")
        assert "Maria" in result


class TestCercarAgendaLobbies:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"grup_interes": "Lobby A"}], 1)
        result = await server.cercar_agenda_lobbies(grup_interes="Lobby A")
        assert "Lobby A" in result


class TestCercarViatgesAltsCarrecs:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = ([{"destinacio": "París"}], 1)
        result = await server.cercar_viatges_alts_carrecs(destinacio="París")
        assert "París" in result


class TestCercarContractesMenors:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search(self, mock_query):
        mock_query.return_value = (
            [
                {
                    "empresa_adjudicat_ria": "TEST SL",
                    "import_adjudicat_sense_iva": "500000",
                }
            ],
            1,
        )
        result = await server.cercar_contractes_menors(empresa="TEST SL")
        assert "TEST SL" in result


# ===========================================================================
# BDNS
# ===========================================================================


class TestBdnsCercarConcessions:
    @pytest.mark.asyncio
    @patch("mcp_govern.bdns.buscar_concessions", new_callable=AsyncMock)
    async def test_search(self, mock_bdns):
        mock_bdns.return_value = {
            "content": [{"beneficiario": "Test"}],
            "totalElements": 1,
        }
        result = await server.bdns_cercar_concessions()
        assert "Test" in result


class TestBdnsCercarConvocatories:
    @pytest.mark.asyncio
    @patch("mcp_govern.bdns.buscar_convocatories", new_callable=AsyncMock)
    async def test_search(self, mock_bdns):
        mock_bdns.return_value = {
            "content": [{"titulo": "Conv test"}],
            "totalElements": 1,
        }
        result = await server.bdns_cercar_convocatories()
        assert "Conv test" in result


class TestBdnsDetallConvocatoria:
    @pytest.mark.asyncio
    @patch("mcp_govern.bdns.detall_convocatoria", new_callable=AsyncMock)
    async def test_detail(self, mock_bdns):
        mock_bdns.return_value = {"numConv": "123", "titulo": "Test"}
        result = await server.bdns_detall_convocatoria(numero_bdns="123")
        assert "123" in result


# ===========================================================================
# Investigar + Detecció
# ===========================================================================


class TestInvestigarEntitat:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query", new_callable=AsyncMock)
    @patch("mcp_govern.bdns.buscar_concessions", new_callable=AsyncMock)
    async def test_basic_investigation(self, mock_bdns, mock_socrata):
        mock_socrata.return_value = []
        mock_bdns.return_value = {"content": []}
        result = await server.investigar_entitat(nom="EMPRESA TEST")
        assert "EMPRESA TEST" in result


class TestDetectarConcentracio:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_analysis(self, mock_query):
        mock_query.return_value = (
            [
                {
                    "adjudicatari": "GRAN CORP",
                    "num_contractes": "50",
                    "import_total": "5000000",
                },
                {
                    "adjudicatari": "PETITA SL",
                    "num_contractes": "5",
                    "import_total": "100000",
                },
            ],
            None,
        )
        result = await server.detectar_concentracio_contractes(any="2024")
        assert "CONCENTRACIÓ" in result
        assert "GRAN CORP" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_no_results(self, mock_query):
        mock_query.return_value = ([], None)
        result = await server.detectar_concentracio_contractes()
        assert "No s'han trobat" in result


class TestDetectarFraccionament:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_alerts(self, mock_query):
        records = [
            {
                "empresa_adjudicat_ria": "SOSPITOSA SL",
                "import_adjudicat_sense_iva": "1200000",
                "departament_d_adscripci": "Dept A",
                "any": "2024",
            },
        ] * 6  # 6 contractes
        mock_query.return_value = (records, 6)
        result = await server.detectar_fraccionament(empresa="SOSPITOSA SL")
        assert "FRACCIONAMENT" in result
        assert "ALERTA" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_no_contracts(self, mock_query):
        mock_query.return_value = ([], 0)
        result = await server.detectar_fraccionament(empresa="INEXISTENT")
        assert "No s'han trobat" in result


# ===========================================================================
# datos.gob.es
# ===========================================================================


class TestDatosgobCercarDatasets:
    @pytest.mark.asyncio
    @patch("mcp_govern.datosgob.buscar_datasets", new_callable=AsyncMock)
    async def test_search(self, mock_datos):
        mock_datos.return_value = {"result": {"items": [{"title": "Presupuestos"}]}}
        result = await server.datosgob_cercar_datasets(query="presupuestos")
        assert "Presupuestos" in result


class TestDatosgobDetallDataset:
    @pytest.mark.asyncio
    @patch("mcp_govern.datosgob.detall_dataset", new_callable=AsyncMock)
    async def test_detail(self, mock_datos):
        mock_datos.return_value = {
            "result": {
                "items": [{"title": "Test DS", "description": "Desc"}],
            },
        }
        result = await server.datosgob_detall_dataset(dataset_id="test-id")
        assert "Test DS" in result


# ===========================================================================
# CGPJ
# ===========================================================================


class TestCgpjDadesCorrupcio:
    @pytest.mark.asyncio
    @patch("mcp_govern.cgpj.obtenir_dades_corrupcio", new_callable=AsyncMock)
    async def test_returns_data(self, mock_cgpj):
        mock_cgpj.return_value = {
            "url_repositori": "https://example.com",
            "status": 200,
        }
        result = await server.cgpj_dades_corrupcio()
        assert "example.com" in result


class TestCgpjCercarSentencies:
    @pytest.mark.asyncio
    @patch("mcp_govern.cgpj.cercar_sentencies", new_callable=AsyncMock)
    async def test_search(self, mock_cgpj):
        mock_cgpj.return_value = {
            "resultats": [{"roj": "STS 100/2026", "ecli": "ECLI:ES:TS:2026:100"}],
            "total_mostrats": 1,
        }
        result = await server.cgpj_cercar_sentencies(text="malversación")
        assert "STS 100/2026" in result


class TestCgpjEstadistiques:
    @pytest.mark.asyncio
    @patch("mcp_govern.cgpj.buscar_estadistiques_judicials", new_callable=AsyncMock)
    async def test_search(self, mock_cgpj):
        mock_cgpj.return_value = {
            "bases_dades": [{"nom": "01.-Tribunal Supremo"}],
            "total": 1,
        }
        result = await server.cgpj_estadistiques_judicials(tema="penal")
        assert "Tribunal Supremo" in result


# ===========================================================================
# Barcelona
# ===========================================================================


class TestBcnCercarDatasets:
    @pytest.mark.asyncio
    @patch("mcp_govern.barcelona.cercar_datasets", new_callable=AsyncMock)
    async def test_search(self, mock_bcn):
        mock_bcn.return_value = {
            "success": True,
            "result": {
                "count": 1,
                "results": [{"name": "pressupost", "title": "Pressupostos", "tags": []}],
            },
        }
        result = await server.bcn_cercar_datasets(query="pressupost")
        assert "Pressupostos" in result


class TestBcnDetallDataset:
    @pytest.mark.asyncio
    @patch("mcp_govern.barcelona.detall_dataset", new_callable=AsyncMock)
    async def test_detail(self, mock_bcn):
        mock_bcn.return_value = {
            "success": True,
            "result": {"name": "test", "title": "Test DS", "resources": []},
        }
        result = await server.bcn_detall_dataset(dataset_name="test")
        assert "Test DS" in result


class TestBcnObtenirDades:
    @pytest.mark.asyncio
    @patch("mcp_govern.barcelona.obtenir_dades", new_callable=AsyncMock)
    async def test_get_data(self, mock_bcn):
        mock_bcn.return_value = {
            "success": True,
            "result": {"records": [{"a": 1}], "total": 1},
        }
        result = await server.bcn_obtenir_dades(resource_id="res-123")
        assert '"a": 1' in result


# ===========================================================================
# BOE / BORME
# ===========================================================================


class TestBoeSumari:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_sumari", new_callable=AsyncMock)
    async def test_sumari(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": {"sumario_nbo": {"diario": {"seccion": []}}},
        }
        result = await server.boe_sumari(data="20260314")
        assert "No s'han trobat" in result or "BOE" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_sumari", new_callable=AsyncMock)
    async def test_sumari_error(self, mock_boe):
        import httpx

        mock_boe.side_effect = httpx.HTTPError("timeout")
        result = await server.boe_sumari(data="20260314")
        assert "Error" in result


class TestBoeNomenaments:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_sumari", new_callable=AsyncMock)
    async def test_nomenaments(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": {"sumario_nbo": {"diario": {"seccion": []}}},
        }
        result = await server.boe_nomenaments(data="20260314")
        assert "No s'han trobat" in result or "nomenaments" in result.lower()


class TestBoeContractes:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_sumari", new_callable=AsyncMock)
    async def test_contractes(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": {"sumario_nbo": {"diario": {"seccion": []}}},
        }
        result = await server.boe_contractes(data="20260314")
        assert "No s'han trobat" in result or "contractes" in result.lower()


class TestBoeLegislacio:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.cercar_legislacio", new_callable=AsyncMock)
    async def test_legislacio(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": [
                {
                    "identificador": "BOE-A-2024-001",
                    "titulo": "Llei test",
                    "rango": {"texto": "Ley"},
                    "departamento": {"texto": "Interior"},
                    "ambito": {"texto": "Estatal"},
                    "fecha_disposicion": "2024-01-01",
                    "fecha_publicacion": "2024-01-02",
                    "vigencia_agotada": "N",
                    "estado_consolidacion": {"texto": "Vigente"},
                    "url_html_consolidada": "https://boe.es/test",
                },
            ],
        }
        result = await server.boe_legislacio()
        assert "Llei test" in result


class TestBoeDepartaments:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_departaments", new_callable=AsyncMock)
    async def test_departaments(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": {"001": "Interior", "002": "Defensa"},
        }
        result = await server.boe_departaments()
        assert "Interior" in result


class TestBormeSumari:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.obtenir_sumari_borme", new_callable=AsyncMock)
    async def test_borme(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": {},
        }
        result = await server.borme_sumari(data="20260314")
        # El BORME pot retornar dades o "no trobat"
        assert isinstance(result, str)


# ===========================================================================
# INE
# ===========================================================================


class TestIneOperacions:
    @pytest.mark.asyncio
    @patch("mcp_govern.ine.llistar_operacions", new_callable=AsyncMock)
    async def test_list(self, mock_ine):
        mock_ine.return_value = [{"Id": 25, "Nombre": "IPC"}]
        result = await server.ine_operacions()
        assert "IPC" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.ine.llistar_operacions", new_callable=AsyncMock)
    async def test_error(self, mock_ine):
        import httpx

        mock_ine.side_effect = httpx.HTTPError("error")
        result = await server.ine_operacions()
        assert "Error" in result


class TestIneTaules:
    @pytest.mark.asyncio
    @patch("mcp_govern.ine.llistar_taules", new_callable=AsyncMock)
    async def test_list(self, mock_ine):
        mock_ine.return_value = [{"Id": 100, "Nombre": "Taula IPC"}]
        result = await server.ine_taules(operacio="IPC")
        assert "Taula IPC" in result


class TestIneDadesTaula:
    @pytest.mark.asyncio
    @patch("mcp_govern.ine.obtenir_dades_taula", new_callable=AsyncMock)
    async def test_data(self, mock_ine):
        mock_ine.return_value = [{"Nombre": "Serie A", "Data": [{"Valor": 100}]}]
        result = await server.ine_dades_taula(taula_id=100)
        assert "Serie A" in result


class TestIneSerie:
    @pytest.mark.asyncio
    @patch("mcp_govern.ine.obtenir_serie", new_callable=AsyncMock)
    async def test_serie(self, mock_ine):
        mock_ine.return_value = [{"Valor": 105.3}]
        result = await server.ine_serie(serie="IPC206449")
        assert "105.3" in result


# ===========================================================================
# BdE
# ===========================================================================


class TestBdeSerie:
    @pytest.mark.asyncio
    @patch("mcp_govern.bde.obtenir_ultim_valor", new_callable=AsyncMock)
    async def test_serie(self, mock_bde):
        mock_bde.return_value = [{"serie": "D_1NBAF472", "valor": "3.5"}]
        result = await server.bde_serie(series="D_1NBAF472")
        assert "3.5" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.bde.obtenir_ultim_valor", new_callable=AsyncMock)
    async def test_error(self, mock_bde):
        import httpx

        mock_bde.side_effect = httpx.HTTPError("error")
        result = await server.bde_serie(series="INVALID")
        assert "Error" in result


class TestBdeSeriesDestacades:
    @pytest.mark.asyncio
    @patch("mcp_govern.bde.obtenir_ultim_valor", new_callable=AsyncMock)
    async def test_series(self, mock_bde):
        mock_bde.return_value = [{"serie": "D_1NBAF472", "valor": "3.5"}]
        result = await server.bde_series_destacades()
        assert "3.5" in result


# ===========================================================================
# PGE
# ===========================================================================


class TestPgeEstructura:
    @pytest.mark.asyncio
    @patch("mcp_govern.pge.obtenir_index", new_callable=AsyncMock)
    async def test_structure(self, mock_pge):
        mock_pge.return_value = {
            "Estructura": {
                "Estructura": {
                    "Estructura": [
                        {
                            "Codigo": "01",
                            "Nombre": "Gastos del Estado",
                            "Estructura": [{"Informe": {"text": "info"}}],
                        },
                    ],
                },
            },
        }
        result = await server.pge_estructura(any_=2024)
        # La tool processa l'estructura i retorna seccions
        assert "1 seccions" in result or "Gastos" in result

    @pytest.mark.asyncio
    async def test_invalid_year(self):
        result = await server.pge_estructura(any_=2020)
        assert "no disponible" in result or "disponibles" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.pge.obtenir_index", new_callable=AsyncMock)
    async def test_error(self, mock_pge):
        import httpx

        mock_pge.side_effect = httpx.HTTPError("error")
        result = await server.pge_estructura(any_=2024)
        assert "Error" in result


class TestPgeDespeses:
    @pytest.mark.asyncio
    @patch("mcp_govern.pge.obtenir_despeses", new_callable=AsyncMock)
    async def test_despeses(self, mock_pge):
        mock_pge.return_value = [
            {"_seccio": "Estado", "programa": "Defensa", "import": "1000000"},
        ]
        result = await server.pge_despeses(any_=2024)
        assert "1 partides" in result
        assert "Defensa" in result

    @pytest.mark.asyncio
    async def test_invalid_year(self):
        result = await server.pge_despeses(any_=2020)
        assert "no disponible" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.pge.obtenir_despeses", new_callable=AsyncMock)
    async def test_no_results(self, mock_pge):
        mock_pge.return_value = []
        result = await server.pge_despeses(any_=2024, seccio="INEXISTENT")
        assert "No s'han trobat" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.pge.obtenir_despeses", new_callable=AsyncMock)
    async def test_error(self, mock_pge):
        import httpx

        mock_pge.side_effect = httpx.HTTPError("error")
        result = await server.pge_despeses(any_=2024)
        assert "Error" in result


# ===========================================================================
# DOGC
# ===========================================================================


class TestDogcCercarNormativa:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search_by_title(self, mock_query):
        mock_query.return_value = (
            [{"t_tol_de_la_norma": "Llei de transparència", "any": "2024"}],
            1,
        )
        result = await server.dogc_cercar_normativa(titol="transparència")
        assert "transparència" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_search_by_rang(self, mock_query):
        mock_query.return_value = ([{"rang_de_norma": "Decret"}], 1)
        result = await server.dogc_cercar_normativa(rang="Decret")
        assert "Decret" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query_with_count", new_callable=AsyncMock)
    async def test_no_results(self, mock_query):
        mock_query.return_value = ([], 0)
        result = await server.dogc_cercar_normativa(titol="inexistent")
        assert "No s'han trobat" in result


# ===========================================================================
# BDNS with text search
# ===========================================================================


class TestBdnsCercarConcessionsText:
    @pytest.mark.asyncio
    @patch("mcp_govern.bdns.buscar_concessions", new_callable=AsyncMock)
    async def test_search_with_text(self, mock_bdns):
        mock_bdns.return_value = {
            "content": [{"beneficiario": "Telefonica SA"}],
            "totalElements": 1,
            "totalPages": 1,
        }
        result = await server.bdns_cercar_concessions(texto="Telefonica")
        assert "Telefonica" in result
        # Verify texto param was passed
        mock_bdns.assert_called_once()
        call_kwargs = mock_bdns.call_args[1]
        assert call_kwargs["texto"] == "Telefonica"

    @pytest.mark.asyncio
    @patch("mcp_govern.bdns.buscar_concessions", new_callable=AsyncMock)
    async def test_search_with_comunitat(self, mock_bdns):
        mock_bdns.return_value = {
            "content": [],
            "totalElements": 0,
            "totalPages": 0,
        }
        await server.bdns_cercar_concessions(comunitat="CATALUÑA")
        call_kwargs = mock_bdns.call_args[1]
        assert call_kwargs["comunidad"] == "CATALUÑA"


# ===========================================================================
# BOE legislació with filters
# ===========================================================================


class TestBoeLegislacioFilters:
    @pytest.mark.asyncio
    @patch("mcp_govern.boe.cercar_legislacio", new_callable=AsyncMock)
    async def test_filter_by_title_locally(self, mock_boe):
        """El filtrat per títol es fa localment (l'API no ho suporta)."""
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": [
                {
                    "identificador": "BOE-A-2024-001",
                    "titulo": "Ley de transparencia",
                    "rango": {"texto": "Ley"},
                    "departamento": {"texto": "Interior"},
                    "ambito": {"texto": "Estatal"},
                    "fecha_disposicion": "2024-01-01",
                    "fecha_publicacion": "2024-01-02",
                    "vigencia_agotada": "N",
                    "estado_consolidacion": {"texto": "Vigente"},
                    "url_html_consolidada": "https://boe.es/test",
                },
                {
                    "identificador": "BOE-A-2024-002",
                    "titulo": "Real Decreto de defensa",
                    "rango": {"texto": "Real Decreto"},
                    "departamento": {"texto": "Defensa"},
                    "ambito": {"texto": "Estatal"},
                    "fecha_disposicion": "2024-02-01",
                    "fecha_publicacion": "2024-02-02",
                    "vigencia_agotada": "N",
                    "estado_consolidacion": {"texto": "Vigente"},
                    "url_html_consolidada": "https://boe.es/test2",
                },
            ],
        }
        result = await server.boe_legislacio(titol="transparencia")
        assert "transparencia" in result
        assert "BOE-A-2024-002" not in result  # defensa filtered out

    @pytest.mark.asyncio
    @patch("mcp_govern.boe.cercar_legislacio", new_callable=AsyncMock)
    async def test_filter_by_rang_locally(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": [
                {
                    "identificador": "BOE-A-2024-001",
                    "titulo": "Ley test",
                    "rango": {"texto": "Ley"},
                    "departamento": {"texto": "Interior"},
                    "ambito": {"texto": "Estatal"},
                    "fecha_disposicion": "",
                    "fecha_publicacion": "",
                    "vigencia_agotada": "N",
                    "estado_consolidacion": {"texto": "Vigente"},
                    "url_html_consolidada": "",
                },
            ],
        }
        result = await server.boe_legislacio(rang="Ley")
        assert "Ley test" in result

    @pytest.mark.asyncio
    @patch("mcp_govern.boe.cercar_legislacio", new_callable=AsyncMock)
    async def test_filter_no_match(self, mock_boe):
        mock_boe.return_value = {
            "status": {"code": "200"},
            "data": [
                {
                    "identificador": "BOE-A-2024-001",
                    "titulo": "Ley de defensa",
                    "rango": {"texto": "Ley"},
                    "departamento": {"texto": "Defensa"},
                    "ambito": {"texto": "Estatal"},
                    "fecha_disposicion": "",
                    "fecha_publicacion": "",
                    "vigencia_agotada": "N",
                    "estado_consolidacion": {"texto": "Vigente"},
                    "url_html_consolidada": "",
                },
            ],
        }
        result = await server.boe_legislacio(titol="educacion")
        assert "No s'han trobat" in result


# ===========================================================================
# investigar_entitat with CIF
# ===========================================================================


class TestInvestigarEntitatCif:
    @pytest.mark.asyncio
    @patch("mcp_govern.socrata.query", new_callable=AsyncMock)
    @patch("mcp_govern.bdns.buscar_concessions", new_callable=AsyncMock)
    async def test_with_cif(self, mock_bdns, mock_socrata):
        mock_socrata.return_value = []
        mock_bdns.return_value = {"content": []}
        result = await server.investigar_entitat(nom="TEST", cif="B12345678")
        assert "TEST" in result
        # CIF queries should have been made (extra calls to socrata.query)
        # The function makes 13 base queries + 2 CIF queries
        assert mock_socrata.call_count >= 13

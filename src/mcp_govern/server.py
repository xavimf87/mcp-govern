"""MCP server per consultar dades obertes del Govern de Catalunya i d'Espanya."""

from __future__ import annotations

import json
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import barcelona, bde, bdns, boe, cgpj, datosgob, ine, pge, socrata
from .datasets import DATASETS

_INSTRUCTIONS = """\
Servidor MCP expert en transparència, dades obertes i detecció de patrons \
de corrupció del Govern de Catalunya i d'Espanya.

FONTS DE DADES:
- Socrata (Catalunya): contractes, subvencions RAISC, retribucions, pressupostos, \
RLT, agenda lobbies, viatges, declaracions activitats.
- BDNS (Espanya): subvencions amb noms reals de beneficiaris (persones físiques i jurídiques).
- datos.gob.es (Espanya): catàleg nacional de dades obertes (113.000+ datasets) \
amb informació de contractació, pressupostos, economia i sector públic.
- CGPJ (Espanya): estadístiques judicials, repositori de processos per corrupció \
i cercador de sentències del CENDOJ.
- Open Data BCN (Barcelona): 553 datasets municipals — pressupostos, contractes, \
seguretat (incidents GUB), transport, medi ambient, habitatge i economia.
- BOE (Espanya): Butlletí Oficial de l'Estat — nomenaments, cessaments, disposicions, \
contractes publicats i legislació consolidada.
- BORME (Espanya): Butlletí Oficial del Registre Mercantil — actes inscrits d'empreses \
per província (constitucions, nomenaments d'administradors, cessaments, dissolucions).
- INE (Espanya): Institut Nacional d'Estadística — 111 operacions estadístiques (IPC, EPA, PIB, etc.).
- Banc d'Espanya: Sèries temporals financeres (Euribor, deute públic, tipus d'interès BCE).
- PGE (Espanya): Pressupostos Generals de l'Estat — despeses i ingressos per ministeris.

ÚS DE LES TOOLS:
- Sou d'un càrrec (president, conseller...): cercar_retribucions_alts_carrecs amb 'carrec'
- Sous amb nom: cercar_retribucions_alts_carrecs amb 'nom'
- Directius entitats públiques: cercar_directius_sector_public
- Taules salarials (mossos, bombers...): consultar_taules_salarials
- Subvencions amb noms reals: bdns_cercar_concessions
- Estadístiques agregades: estadistiques (usa llistar_camps abans)
- Investigació completa d'una entitat/persona: investigar_entitat
- Datasets nacionals d'Espanya: datosgob_cercar_datasets + datosgob_detall_dataset
- Dades de corrupció judicial: cgpj_dades_corrupcio
- Sentències judicials: cgpj_cercar_sentencies
- Estadístiques judicials: cgpj_estadistiques_judicials
- Dades de Barcelona: bcn_cercar_datasets, bcn_detall_dataset, bcn_obtenir_dades
- Nomenaments i cessaments oficials: boe_sumari (secció 2A)
- Contractes publicats al BOE: boe_sumari (secció 5A)
- Legislació consolidada: boe_legislacio
- Registre mercantil (BORME): borme_sumari (actes d'empreses per província)
- Estadístiques INE (IPC, EPA...): ine_operacions, ine_taules, ine_dades_taula
- Dades financeres BdE (Euribor...): bde_serie, bde_series_destacades
- Pressupostos de l'Estat (PGE): pge_estructura

PATRONS DE CORRUPCIÓ — Quan l'usuari demani investigar o analitzar, aplica \
proactivament aquestes estratègies:

1. FRACCIONAMENT DE CONTRACTES
   Detectar si una entitat rep molts contractes menors (< 15.000€ serveis, \
   < 40.000€ obres) del mateix departament. Indica possible fraccionament \
   per evitar licitació pública.
   → cercar_contractes_menors filtrant per empresa, i estadistiques per comptar.

2. PORTA GIRATÒRIA (REVOLVING DOOR)
   Creuar alts càrrecs cessats (declaracions_activitats amb situaci_carrec='Inactiu') \
   amb empreses que reben contractes o subvencions poc després.
   → cercar_declaracions_activitats + cercar_contractes / cercar_subvencions

3. LOBBY → CONTRACTE
   Correlacionar reunions amb grups d'interès i contractes/subvencions adjudicats \
   poc després al mateix sector o entitat.
   → cercar_agenda_lobbies + cercar_contractes / cercar_subvencions

4. CONCENTRACIÓ DE PROVEÏDORS
   Identificar empreses que acumulen un % anòmal del volum de contractació d'un \
   departament o organisme.
   → estadistiques agrupant per adjudicatari + cercar_contractes per detalls

5. RETRIBUCIONS ANÒMALES
   Directius d'entitats subvencionades que cobren per sobre dels alts càrrecs \
   de la Generalitat.
   → cercar_retribucions_subvencionats vs cercar_retribucions_alts_carrecs

6. SUBVENCIONS OPAQUES
   Beneficiaris que apareixen com "Benef. no publicable" a RAISC (Socrata) però \
   que sí es poden identificar a la BDNS. Creuar codi_bdns entre ambdues fonts.
   → cercar_subvencions + bdns_cercar_concessions

7. VIATGES SOSPITOSOS
   Viatges a l'estranger amb despeses desproporcionades, sense motiu clar, o a \
   destinacions no relacionades amb la funció.
   → cercar_viatges_alts_carrecs

8. NEPOTISME EN LLOCS DE TREBALL
   Llocs de treball eventual o de lliure designació concentrats en un departament.
   → cercar_llocs_treball amb prov_lloc='LD' (lliure designació)

IMPORTANT: Quan presentes resultats d'investigació:
- Basa't NOMÉS en dades verificables retornades per les tools.
- Distingeix clarament entre FETS (dades) i INDICIS (patrons sospitosos).
- No acusis directament — presenta els patrons i deixa que l'usuari tregui conclusions.
- Suggereix sempre línies d'investigació addicionals per aprofundir.
- Usa la tool investigar_entitat per fer un perfil complet ràpidament.
"""

mcp = FastMCP("mcp-govern", instructions=_INSTRUCTIONS)


def _fmt(records: list[dict], total: int | None = None, limit: int = 50, offset: int = 0) -> str:
    """Formata els resultats com a JSON llegible, indicant el total disponible."""
    if not records:
        return "No s'han trobat resultats."
    header = ""
    if total is not None:
        shown = len(records)
        if total > shown:
            header = (
                f"Mostrant {offset + 1}-{offset + shown} de {total} resultats totals. "
                f"Hi ha {total - offset - shown} resultats més. "
                f"Afina la cerca amb filtres o augmenta el limit/offset per veure'ls.\n\n"
            )
        else:
            header = f"Total: {total} resultats.\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


def _build_where(clauses: list[str]) -> str | None:
    """Combina clàusules WHERE amb AND."""
    parts = [c for c in clauses if c]
    return " AND ".join(parts) if parts else None


def _fix_import_centims(records: list[dict], camp: str) -> list[dict]:
    """Converteix imports que venen en cèntims a euros.

    El dataset de contractes menors (`qjue-2pk9`) retorna els imports
    en cèntims d'euro en lloc d'euros. Aquesta funció els divideix per 100.
    """
    for r in records:
        try:
            val = r.get(camp)
            if val is not None:
                r[camp] = str(round(float(val) / 100, 2))
        except (ValueError, TypeError):
            pass
    return records


# ---------------------------------------------------------------------------
# Tool 0: Llistar camps d'un dataset
# ---------------------------------------------------------------------------
@mcp.tool()
async def llistar_camps(
    dataset: Annotated[str, Field(description="Dataset: 'contractes', 'pscp', 'subvencions' o 'convocatories'")],
) -> str:
    """Retorna els camps disponibles d'un dataset.

    Utilitza aquesta tool ABANS de fer consultes amb 'estadistiques'
    per conèixer els noms exactes dels camps (agrupar_per, camp_suma, filtre).
    """
    info = DATASETS.get(dataset)
    if not info:
        return f"Error: dataset '{dataset}' no trobat. Opcions: {', '.join(DATASETS.keys())}"
    lines = [f"Dataset: {info['nom']}", f"ID: {info['id']}", "", "Camps disponibles:"]
    for camp in info["camps"]:
        lines.append(f"  - {camp}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 1: Cercar contractes (Registre públic)
# ---------------------------------------------------------------------------
@mcp.tool()
async def cercar_contractes(
    exercici: Annotated[str | None, Field(description="Any de l'exercici (ex: '2024')")] = None,
    tipus_contracte: Annotated[str | None, Field(description="Tipus de contracte (ex: '5. SERVEIS', '1. OBRES', '3. SUBMINISTRAMENTS')")] = None,
    adjudicatari: Annotated[str | None, Field(description="Nom o part del nom de l'adjudicatari")] = None,
    organisme: Annotated[str | None, Field(description="Nom o part del nom de l'organisme contractant")] = None,
    import_minim: Annotated[float | None, Field(description="Import mínim d'adjudicació (€)")] = None,
    import_maxim: Annotated[float | None, Field(description="Import màxim d'adjudicació (€)")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure per cercar a tots els camps")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats (per defecte 50, màxim 50000)")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca contractes públics al Registre públic de contractes de Catalunya.

    Permet filtrar per any, tipus, adjudicatari, organisme i import.
    Les dades inclouen: codi d'expedient, descripció, adjudicatari, import, data, durada, etc.
    """
    clauses = []
    if exercici:
        clauses.append(f"exercici='{exercici}'")
    if tipus_contracte:
        clauses.append(f"tipus_contracte='{tipus_contracte}'")
    if adjudicatari:
        clauses.append(f"upper(adjudicatari) like upper('%{adjudicatari}%')")
    if organisme:
        clauses.append(f"upper(organisme_contractant) like upper('%{organisme}%')")
    if import_minim is not None:
        clauses.append(f"import_adjudicacio >= '{import_minim}'")
    if import_maxim is not None:
        clauses.append(f"import_adjudicacio <= '{import_maxim}'")

    records, total = await socrata.query_with_count(
        "contractes",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="data_adjudicacio DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


# ---------------------------------------------------------------------------
# Tool 2: Cercar publicacions PSCP
# ---------------------------------------------------------------------------
@mcp.tool()
async def cercar_publicacions_pscp(
    objecte: Annotated[str | None, Field(description="Text a cercar a l'objecte del contracte")] = None,
    nom_organ: Annotated[str | None, Field(description="Nom de l'òrgan contractant")] = None,
    tipus_contracte: Annotated[str | None, Field(description="Tipus de contracte")] = None,
    fase: Annotated[str | None, Field(description="Fase de publicació (ex: 'Adjudicació', 'Formalització', 'Anunci previ')")] = None,
    adjudicatari: Annotated[str | None, Field(description="Nom o part del nom de l'adjudicatari")] = None,
    import_minim: Annotated[float | None, Field(description="Import mínim d'adjudicació amb IVA (€)")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure per cercar a tots els camps")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats (per defecte 50)")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca publicacions a la Plataforma de Serveis de Contractació Pública (PSCP).

    Inclou licitacions, adjudicacions i formalitzacions publicades.
    Camps: òrgan, objecte, tipus, fase, adjudicatari, imports (amb i sense IVA), dates, enllaç.
    """
    clauses = []
    if objecte:
        clauses.append(f"upper(objecte_contracte) like upper('%{objecte}%')")
    if nom_organ:
        clauses.append(f"upper(nom_organ) like upper('%{nom_organ}%')")
    if tipus_contracte:
        clauses.append(f"tipus_contracte='{tipus_contracte}'")
    if fase:
        clauses.append(f"upper(fase_publicacio) like upper('%{fase}%')")
    if adjudicatari:
        clauses.append(f"upper(denominacio_adjudicatari) like upper('%{adjudicatari}%')")
    if import_minim is not None:
        clauses.append(f"import_adjudicacio_amb_iva >= '{import_minim}'")

    records, total = await socrata.query_with_count(
        "pscp",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="data_publicacio_contracte DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


# ---------------------------------------------------------------------------
# Tool 3: Cercar subvencions (RAISC)
# ---------------------------------------------------------------------------
@mcp.tool()
async def cercar_subvencions(
    any_convocatoria: Annotated[str | None, Field(description="Any de la convocatòria (ex: '2024')")] = None,
    beneficiari: Annotated[str | None, Field(description="Nom o part del nom del beneficiari")] = None,
    cif_beneficiari: Annotated[str | None, Field(description="CIF/NIF del beneficiari")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament o entitat")] = None,
    finalitat: Annotated[str | None, Field(description="Finalitat pública de la subvenció")] = None,
    import_minim: Annotated[float | None, Field(description="Import mínim de la subvenció (€)")] = None,
    import_maxim: Annotated[float | None, Field(description="Import màxim de la subvenció (€)")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure per cercar a tots els camps")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats (per defecte 50)")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca subvencions i ajuts concedits al RAISC (Registre d'Ajuts i Subvencions de Catalunya).

    Permet filtrar per any, beneficiari, departament, finalitat i import.
    Camps: codi RAISC/BDNS, objecte, beneficiari, CIF, import, data concessió, etc.
    """
    clauses = []
    if any_convocatoria:
        clauses.append(f"any_de_la_convocat_ria='{any_convocatoria}'")
    if beneficiari:
        clauses.append(f"upper(ra_social_del_beneficiari) like upper('%{beneficiari}%')")
    if cif_beneficiari:
        clauses.append(f"cif_beneficiari='{cif_beneficiari}'")
    if departament:
        clauses.append(f"upper(entitat_oo_aa_o_departament_1) like upper('%{departament}%')")
    if finalitat:
        clauses.append(f"upper(finalitat_p_blica) like upper('%{finalitat}%')")
    if import_minim is not None:
        clauses.append(f"import_subvenci_pr_stec_ajut >= '{import_minim}'")
    if import_maxim is not None:
        clauses.append(f"import_subvenci_pr_stec_ajut <= '{import_maxim}'")

    records, total = await socrata.query_with_count(
        "subvencions",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="data_concessi DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


# ---------------------------------------------------------------------------
# Tool 4: Cercar convocatòries
# ---------------------------------------------------------------------------
@mcp.tool()
async def cercar_convocatories(
    any_convocatoria: Annotated[str | None, Field(description="Any de la convocatòria (ex: '2024')")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament o entitat")] = None,
    finalitat: Annotated[str | None, Field(description="Finalitat pública de la convocatòria")] = None,
    tipus_beneficiaris: Annotated[str | None, Field(description="Tipus de beneficiaris")] = None,
    import_minim: Annotated[float | None, Field(description="Import total mínim de la convocatòria (€)")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure per cercar a tots els camps")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats (per defecte 50)")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca convocatòries de subvencions al RAISC.

    Permet filtrar per any, departament, finalitat i import.
    Camps: codi RAISC/BDNS, títol, objecte, tipus beneficiaris, imports, dates sol·licitud, etc.
    """
    clauses = []
    if any_convocatoria:
        clauses.append(f"any_de_la_convocat_ria='{any_convocatoria}'")
    if departament:
        clauses.append(f"upper(entitat_oo_aa_o_departament_1) like upper('%{departament}%')")
    if finalitat:
        clauses.append(f"upper(finalitat_publica) like upper('%{finalitat}%')")
    if tipus_beneficiaris:
        clauses.append(f"upper(tipus_de_beneficiaris) like upper('%{tipus_beneficiaris}%')")
    if import_minim is not None:
        clauses.append(f"import_total_convocat_ria >= '{import_minim}'")

    records, total = await socrata.query_with_count(
        "convocatories",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="any_de_la_convocat_ria DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


# ---------------------------------------------------------------------------
# Tool 5: Detall contracte
# ---------------------------------------------------------------------------
@mcp.tool()
async def detall_contracte(
    codi_expedient: Annotated[str, Field(description="Codi de l'expedient del contracte")],
) -> str:
    """Obté el detall complet d'un contracte a partir del seu codi d'expedient.

    Retorna tots els lots i la informació completa del contracte.
    """
    records, total = await socrata.query_with_count(
        "contractes",
        where=f"codi_expedient='{codi_expedient}'",
        limit=100,
    )
    return _fmt(records, total)


# ---------------------------------------------------------------------------
# Tool 6: Detall subvenció
# ---------------------------------------------------------------------------
@mcp.tool()
async def detall_subvencio(
    codi_raisc: Annotated[str | None, Field(description="Codi RAISC de la subvenció")] = None,
    codi_bdns: Annotated[str | None, Field(description="Codi BDNS de la subvenció")] = None,
) -> str:
    """Obté el detall complet d'una subvenció a partir del codi RAISC o BDNS.

    Cal proporcionar almenys un dels dos codis.
    """
    if not codi_raisc and not codi_bdns:
        return "Error: cal proporcionar codi_raisc o codi_bdns."

    clauses = []
    if codi_raisc:
        clauses.append(f"codi_raisc='{codi_raisc}'")
    if codi_bdns:
        clauses.append(f"codi_bdns='{codi_bdns}'")

    records, total = await socrata.query_with_count(
        "subvencions",
        where=_build_where(clauses),
        limit=100,
    )
    return _fmt(records, total)


# ---------------------------------------------------------------------------
# Tool 7: Estadístiques
# ---------------------------------------------------------------------------
@mcp.tool()
async def estadistiques(
    dataset: Annotated[str, Field(description="Qualsevol dataset disponible. Usa 'llistar_camps' per veure les opcions.")],
    agrupar_per: Annotated[str, Field(description="Camp pel qual agrupar (ex: 'tipus_contracte', 'exercici', 'entitat_oo_aa_o_departament_1')")],
    operacio: Annotated[str, Field(description="Operació d'agregació: 'count' o 'sum'")] = "count",
    camp_suma: Annotated[str | None, Field(description="Camp numèric per sumar (requerit si operacio='sum', ex: 'import_adjudicacio')")] = None,
    filtre: Annotated[str | None, Field(description="Filtre SoQL opcional (ex: \"exercici='2024'\")")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de grups a retornar")] = 50,
) -> str:
    """Genera estadístiques agregades sobre contractes o subvencions.

    IMPORTANT: Els noms de camp són els interns de Socrata. Usa 'llistar_camps' per consultar-los.

    Camps habituals per agrupar i sumar:
    - contractes: exercici, tipus_contracte, organisme_contractant, adjudicatari | import: import_adjudicacio
    - pscp: nom_organ, tipus_contracte, fase_publicacio, denominacio_adjudicatari | import: import_adjudicacio_amb_iva
    - subvencions: any_de_la_convocat_ria, ra_social_del_beneficiari, entitat_oo_aa_o_departament_1 | import: import_subvenci_pr_stec_ajut
    - convocatories: any_de_la_convocat_ria, entitat_oo_aa_o_departament_1, finalitat_publica | import: import_total_convocat_ria

    Exemples:
    - Contractes per tipus: agrupar_per='tipus_contracte'
    - Top beneficiaris subvencions 2024: dataset='subvencions', agrupar_per='ra_social_del_beneficiari', operacio='sum', camp_suma='import_subvenci_pr_stec_ajut', filtre="any_de_la_convocat_ria='2024'"
    """
    if dataset not in DATASETS:
        return f"Error: dataset no trobat. Opcions: {', '.join(DATASETS.keys())}"

    if operacio == "sum":
        if not camp_suma:
            return "Error: cal especificar camp_suma quan operacio='sum'."
        select = f"{agrupar_per}, sum({camp_suma}) as total"
    else:
        select = f"{agrupar_per}, count(*) as total"

    order = "total DESC"

    records, total = await socrata.query_with_count(
        dataset,
        select=select,
        where=filtre,
        group=agrupar_per,
        order=order,
        limit=limit,
    )
    return _fmt(records, total)


# ===========================================================================
# RETRIBUCIONS I SOUS
# ===========================================================================


@mcp.tool()
async def cercar_retribucions_alts_carrecs(
    nom: Annotated[str | None, Field(description="Nom o cognoms de la persona (cerca parcial)")] = None,
    carrec: Annotated[str | None, Field(description="Denominació del càrrec (ex: 'President', 'Conseller', 'Director general', 'Secretari')")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    vinculacio: Annotated[str | None, Field(description="Tipus de vinculació (ex: 'Alts càrrecs', 'Personal directiu')")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure per cercar a tots els camps")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca retribucions nominals d'alts càrrecs de la Generalitat.

    Retorna NOM, COGNOMS, càrrec (denominacio_lloc), departament i retribució anual prevista.
    Inclou president, consellers, secretaris generals, directors generals, etc.

    Per cercar per càrrec (ex: "president de la generalitat", "conseller"), usa el paràmetre 'carrec'.
    Per cercar per nom de persona, usa 'nom'.
    NOTA: el camp retribucio_anual_prevista és text, l'ordenació pot no ser numèrica exacta.
    """
    clauses = []
    if nom:
        clauses.append(f"upper(cognoms_nom) like upper('%{nom}%')")
    if carrec:
        clauses.append(f"upper(denominacio_lloc) like upper('%{carrec}%')")
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")
    if vinculacio:
        clauses.append(f"upper(vinculacio) like upper('%{vinculacio}%')")

    records, total = await socrata.query_with_count(
        "retrib_alts_carrecs",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="retribucio_anual_prevista DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_directius_sector_public(
    nom: Annotated[str | None, Field(description="Nom o cognoms de la persona")] = None,
    carrec: Annotated[str | None, Field(description="Denominació del càrrec (ex: 'Director', 'Gerent', 'President')")] = None,
    entitat: Annotated[str | None, Field(description="Nom de l'entitat pública")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca retribucions del personal directiu d'entitats del sector públic.

    Retorna NOM, càrrec (denominaci_del_lloc), entitat, departament i retribució fixa anual.
    Cobreix entitats com: ICF, ICAEN, TVC, hospitals públics, etc.
    """
    clauses = []
    if nom:
        clauses.append(f"upper(cognoms_i_nom) like upper('%{nom}%')")
    if carrec:
        clauses.append(f"upper(denominaci_del_lloc) like upper('%{carrec}%')")
    if entitat:
        clauses.append(f"upper(entitat) like upper('%{entitat}%')")
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")

    records, total = await socrata.query_with_count(
        "retrib_directius_sector_public",
        where=_build_where(clauses),
        order="retribuci_fixa_anual_prevista DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_retribucions_subvencionats(
    empresa: Annotated[str | None, Field(description="Nom de l'entitat subvencionada")] = None,
    carrec: Annotated[str | None, Field(description="Càrrec (ex: 'President', 'Director')")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca retribucions dels directius d'entitats que reben subvencions >10.000€.

    Retorna: entitat, càrrec, retribucions anuals, objecte de la subvenció.
    """
    clauses = []
    if empresa:
        clauses.append(f"upper(empresa) like upper('%{empresa}%')")
    if carrec:
        clauses.append(f"upper(c_rrec) like upper('%{carrec}%')")

    records, total = await socrata.query_with_count(
        "retrib_directius_subvencionats",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="retribucions_anuals DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def consultar_taules_salarials(
    cos: Annotated[str, Field(description="Cos: 'alts_carrecs', 'funcionaris', 'laborals', 'mossos', 'bombers', 'agents_rurals', 'penitenciaris'")],
    any: Annotated[str | None, Field(description="Any (ex: '2024')")] = None,
    categoria: Annotated[str | None, Field(description="Categoria professional (per a mossos, bombers, etc.)")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
) -> str:
    """Consulta les taules salarials oficials per cos de la Generalitat.

    Retorna: grup, nivell, sou base, complements i total mensual/anual.
    Per a 'alts_carrecs': retorna sou del president, consellers, secretaris i directors generals.
    Cossos disponibles: alts_carrecs, funcionaris, laborals, mossos, bombers, agents_rurals, penitenciaris.
    """
    dataset_map = {
        "alts_carrecs": "taules_retrib_alts_carrecs",
        "funcionaris": "retrib_funcionaris",
        "laborals": "retrib_laborals",
        "mossos": "retrib_mossos",
        "bombers": "retrib_bombers",
        "agents_rurals": "retrib_agents_rurals",
        "penitenciaris": "retrib_penitenciaris",
    }
    dataset_key = dataset_map.get(cos)
    if not dataset_key:
        return f"Error: cos no trobat. Opcions: {', '.join(dataset_map.keys())}"

    clauses = []
    if any:
        clauses.append(f"any='{any}'")
    if categoria and dataset_key != "taules_retrib_alts_carrecs":
        clauses.append(f"upper(categoria) like upper('%{categoria}%')")

    order = "any DESC" if dataset_key == "taules_retrib_alts_carrecs" else "total_anual DESC"

    records, total = await socrata.query_with_count(
        dataset_key,
        where=_build_where(clauses),
        order=order,
        limit=limit,
    )
    return _fmt(records, total)


# ===========================================================================
# PRESSUPOSTOS
# ===========================================================================


@mcp.tool()
async def cercar_pressupostos(
    exercici: Annotated[str | None, Field(description="Any de l'exercici (ex: '2024')")] = None,
    departament: Annotated[str | None, Field(description="Nom del servei o entitat")] = None,
    programa: Annotated[str | None, Field(description="Nom del programa pressupostari")] = None,
    tipus: Annotated[str | None, Field(description="'I' per ingressos, 'D' per despeses")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca pressupostos aprovats de la Generalitat de Catalunya.

    Retorna: exercici, servei/entitat, programa, capítol, article, concepte i imports.
    """
    clauses = []
    if exercici:
        clauses.append(f"exercici='{exercici}'")
    if departament:
        clauses.append(f"upper(nom_servei_entitat) like upper('%{departament}%')")
    if programa:
        clauses.append(f"upper(nom_programa) like upper('%{programa}%')")
    if tipus:
        clauses.append(f"ingr_s_despesa='{tipus}'")

    records, total = await socrata.query_with_count(
        "pressupostos",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="import_sense_consolidar DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_pressupostos_municipals(
    municipi: Annotated[str | None, Field(description="Nom del municipi")] = None,
    any_exercici: Annotated[str | None, Field(description="Any de l'exercici")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca pressupostos dels ens municipals de Catalunya.

    Retorna: municipi, any, partida, descripció i import.
    """
    clauses = []
    if municipi:
        clauses.append(f"upper(nom_complert) like upper('%{municipi}%')")
    if any_exercici:
        clauses.append(f"any_exercici='{any_exercici}'")

    records, total = await socrata.query_with_count(
        "pressupostos_municipals",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="import DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


# ===========================================================================
# PERSONAL I LLOCS DE TREBALL
# ===========================================================================


@mcp.tool()
async def cercar_llocs_treball(
    tipus: Annotated[str, Field(description="Tipus de personal: 'funcionaris' o 'laborals'")] = "funcionaris",
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    nom_lloc: Annotated[str | None, Field(description="Nom del lloc de treball")] = None,
    localitat: Annotated[str | None, Field(description="Localitat")] = None,
    any: Annotated[str | None, Field(description="Any")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca a la Relació de Llocs de Treball (RLT) de la Generalitat.

    Retorna: departament, nom del lloc, nivell, grup, localitat, jornada, etc.
    """
    dataset_key = "rlt_funcionaris" if tipus == "funcionaris" else "rlt_laborals"
    clauses = []
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")
    if nom_lloc:
        clauses.append(f"upper(nom_lloc) like upper('%{nom_lloc}%')")
    if localitat:
        clauses.append(f"upper(localitat) like upper('%{localitat}%')")
    if any:
        clauses.append(f"any='{any}'")

    records, total = await socrata.query_with_count(
        dataset_key,
        where=_build_where(clauses),
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_oferta_ocupacio(
    any: Annotated[str | None, Field(description="Any de l'oferta")] = None,
    cos: Annotated[str | None, Field(description="Nom del cos o escala")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
) -> str:
    """Cerca l'oferta d'ocupació pública de la Generalitat.

    Retorna: any, cos, escala, grup, places ofertades, tipus d'oferta.
    """
    clauses = []
    if any:
        clauses.append(f"any='{any}'")
    if cos:
        clauses.append(f"upper(cos) like upper('%{cos}%')")

    records, total = await socrata.query_with_count(
        "oferta_ocupacio",
        where=_build_where(clauses),
        order="any DESC, places DESC",
        limit=limit,
    )
    return _fmt(records, total)


# ===========================================================================
# TRANSPARÈNCIA - ALTS CÀRRECS
# ===========================================================================


@mcp.tool()
async def cercar_declaracions_activitats(
    nom: Annotated[str | None, Field(description="Nom o cognoms de l'alt càrrec")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    carrec: Annotated[str | None, Field(description="Denominació del càrrec")] = None,
    actiu: Annotated[bool | None, Field(description="True per càrrecs actius, False per inactius")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca declaracions d'activitats públiques i privades d'alts càrrecs.

    Retorna: nom, departament, càrrec, activitats al sector públic,
    participacions en consells, representacions, patrimoni, etc.
    """
    clauses = []
    if nom:
        clauses.append(
            f"(upper(nom) like upper('%{nom}%') OR "
            f"upper(primer_cognom) like upper('%{nom}%') OR "
            f"upper(segon_cognom) like upper('%{nom}%'))"
        )
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")
    if carrec:
        clauses.append(f"upper(carrec) like upper('%{carrec}%')")
    if actiu is not None:
        clauses.append(f"situaci_carrec='{'Actiu' if actiu else 'Inactiu'}'")

    records, total = await socrata.query_with_count(
        "declaracions_activitats",
        where=_build_where(clauses),
        order="data_nomenament DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_agenda_lobbies(
    alt_carrec: Annotated[str | None, Field(description="Nom de l'alt càrrec")] = None,
    grup_interes: Annotated[str | None, Field(description="Nom del grup d'interès (lobby)")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    tema: Annotated[str | None, Field(description="Tema de la reunió")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca reunions d'alts càrrecs amb grups d'interès (lobbies).

    Retorna: data, alt càrrec, càrrec, grup d'interès, tema, activitat.
    """
    clauses = []
    if alt_carrec:
        clauses.append(f"upper(nom_i_cognoms) like upper('%{alt_carrec}%')")
    if grup_interes:
        clauses.append(f"upper(nom_registre_grup_inter_s) like upper('%{grup_interes}%')")
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")
    if tema:
        clauses.append(f"upper(tema) like upper('%{tema}%')")

    records, total = await socrata.query_with_count(
        "agenda_lobbies",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="data DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_viatges_alts_carrecs(
    nom: Annotated[str | None, Field(description="Nom de l'alt càrrec")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    destinacio: Annotated[str | None, Field(description="País o ciutat de destinació")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca viatges a l'estranger d'alts càrrecs de la Generalitat.

    Retorna: nom, càrrec, destinació, motiu, dates, despeses desglossades
    (dietes, allotjament, transport) i total.
    """
    clauses = []
    if nom:
        clauses.append(f"upper(nom_i_cognoms) like upper('%{nom}%')")
    if departament:
        clauses.append(f"upper(departament) like upper('%{departament}%')")
    if destinacio:
        clauses.append(f"upper(destinaci) like upper('%{destinacio}%')")

    records, total = await socrata.query_with_count(
        "viatges_alts_carrecs",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="inici_viatge DESC",
        limit=limit,
        offset=offset,
    )
    return _fmt(records, total, limit, offset)


@mcp.tool()
async def cercar_contractes_menors(
    any: Annotated[str | None, Field(description="Any (ex: '2024')")] = None,
    empresa: Annotated[str | None, Field(description="Nom de l'empresa adjudicatària")] = None,
    departament: Annotated[str | None, Field(description="Nom del departament")] = None,
    objecte: Annotated[str | None, Field(description="Objecte del contracte")] = None,
    cerca_lliure: Annotated[str | None, Field(description="Text lliure")] = None,
    limit: Annotated[int, Field(description="Nombre màxim de resultats")] = 50,
    offset: Annotated[int, Field(description="Desplaçament per a paginació")] = 0,
) -> str:
    """Cerca contractes menors de la Generalitat de Catalunya.

    Contractes menors: adjudicació directa sense publicitat.
    Retorna: any, departament, objecte, empresa adjudicatària, import.
    """
    clauses = []
    if any:
        clauses.append(f"any='{any}'")
    if empresa:
        clauses.append(f"upper(empresa_adjudicat_ria) like upper('%{empresa}%')")
    if departament:
        clauses.append(f"upper(departament_d_adscripci) like upper('%{departament}%')")
    if objecte:
        clauses.append(f"upper(objecte_del_contracte) like upper('%{objecte}%')")

    records, total = await socrata.query_with_count(
        "contractes_menors",
        where=_build_where(clauses),
        q=cerca_lliure,
        order="import_adjudicat_sense_iva DESC",
        limit=limit,
        offset=offset,
    )
    _fix_import_centims(records, "import_adjudicat_sense_iva")
    return _fmt(records, total, limit, offset)


# ===========================================================================
# BDNS — Base de Datos Nacional de Subvenciones
# ===========================================================================


# ---------------------------------------------------------------------------
# Tool BDNS 1: Cercar concessions
# ---------------------------------------------------------------------------
@mcp.tool()
async def bdns_cercar_concessions(
    data_desde: Annotated[str | None, Field(description="Data inici en format DD/MM/YYYY (ex: '01/01/2026')")] = None,
    data_fins: Annotated[str | None, Field(description="Data fi en format DD/MM/YYYY (ex: '31/12/2026')")] = None,
    pagina: Annotated[int, Field(description="Número de pàgina (0 = primera)")] = 0,
    resultats_per_pagina: Annotated[int, Field(description="Resultats per pàgina (per defecte 50, màxim 200)")] = 50,
) -> str:
    """Cerca concessions (subvencions atorgades) a la BDNS de tota Espanya.

    INCLOU NOMS REALS de beneficiaris (persones físiques i jurídiques).
    Filtra per rang de dates de concessió. Retorna: beneficiari, import,
    convocatòria, nivell administratiu (estatal/autonòmic/local), instrument.

    Per a resultats de Catalunya, filtra els resultats on nivel2='CATALUÑA'.
    """
    result = await bdns.buscar_concessions(
        fecha_desde=data_desde,
        fecha_hasta=data_fins,
        page=pagina,
        page_size=min(resultats_per_pagina, 200),
    )
    total = result.get("totalElements", 0)
    content = result.get("content", [])
    summary = f"Total resultats: {total} | Pàgina {pagina + 1} de {result.get('totalPages', 0)}\n\n"
    return summary + json.dumps(content, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool BDNS 2: Cercar convocatòries BDNS
# ---------------------------------------------------------------------------
@mcp.tool()
async def bdns_cercar_convocatories(
    data_desde: Annotated[str | None, Field(description="Data inici en format DD/MM/YYYY")] = None,
    data_fins: Annotated[str | None, Field(description="Data fi en format DD/MM/YYYY")] = None,
    pagina: Annotated[int, Field(description="Número de pàgina (0 = primera)")] = 0,
    resultats_per_pagina: Annotated[int, Field(description="Resultats per pàgina (per defecte 50)")] = 50,
) -> str:
    """Cerca convocatòries de subvencions a la BDNS.

    Retorna: codi BDNS, descripció, òrgan convocant, imports, dates.
    """
    result = await bdns.buscar_convocatories(
        fecha_desde=data_desde,
        fecha_hasta=data_fins,
        page=pagina,
        page_size=min(resultats_per_pagina, 200),
    )
    total = result.get("totalElements", 0)
    content = result.get("content", [])
    summary = f"Total resultats: {total} | Pàgina {pagina + 1} de {result.get('totalPages', 0)}\n\n"
    return summary + json.dumps(content, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool BDNS 3: Detall convocatòria BDNS
# ---------------------------------------------------------------------------
@mcp.tool()
async def bdns_detall_convocatoria(
    numero_bdns: Annotated[str, Field(description="Número BDNS de la convocatòria (ex: '770776')")],
) -> str:
    """Obté el detall complet d'una convocatòria de la BDNS.

    Inclou: descripció, òrgan, pressupost, tipus beneficiaris, sectors,
    regions, dates sol·licitud, documents, bases reguladores, etc.
    """
    result = await bdns.detall_convocatoria(numero_bdns)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ===========================================================================
# INVESTIGACIÓ — Tools de creuament de dades
# ===========================================================================


@mcp.tool()
async def investigar_entitat(
    nom: Annotated[str, Field(description="Nom de l'empresa, entitat, persona o organisme a investigar")],
    limit_per_font: Annotated[int, Field(description="Resultats màxims per font de dades")] = 50,
) -> str:
    """Investiga una entitat o persona creuant TOTES les fonts de dades disponibles.

    Cerca simultàniament a: contractes, contractes menors, PSCP, subvencions,
    retribucions de directius subvencionats, agenda de lobbies i BDNS.

    Retorna un informe complet amb totes les aparicions trobades.
    Ideal per investigar empreses, persones o organismes sospitosos.
    """
    import asyncio

    results: dict[str, list[dict]] = {}

    # Llançar totes les consultes en paral·lel
    queries = {
        "contractes_registre": socrata.query(
            "contractes",
            where=f"upper(adjudicatari) like upper('%{nom}%')",
            order="data_adjudicacio DESC",
            limit=limit_per_font,
        ),
        "contractes_menors": socrata.query(
            "contractes_menors",
            where=f"upper(empresa_adjudicat_ria) like upper('%{nom}%')",
            order="import_adjudicat_sense_iva DESC",
            limit=limit_per_font,
        ),
        "pscp": socrata.query(
            "pscp",
            where=f"upper(denominacio_adjudicatari) like upper('%{nom}%')",
            order="data_publicacio_contracte DESC",
            limit=limit_per_font,
        ),
        "subvencions_raisc": socrata.query(
            "subvencions",
            where=f"upper(ra_social_del_beneficiari) like upper('%{nom}%')",
            order="data_concessi DESC",
            limit=limit_per_font,
        ),
        "retrib_directius_subvencionats": socrata.query(
            "retrib_directius_subvencionats",
            where=f"upper(empresa) like upper('%{nom}%')",
            order="retribucions_anuals DESC",
            limit=limit_per_font,
        ),
        "agenda_lobbies": socrata.query(
            "agenda_lobbies",
            where=f"upper(nom_registre_grup_inter_s) like upper('%{nom}%')",
            order="data DESC",
            limit=limit_per_font,
        ),
        "alts_carrecs": socrata.query(
            "retrib_alts_carrecs",
            where=f"upper(cognoms_nom) like upper('%{nom}%')",
            order="retribucio_anual_prevista DESC",
            limit=limit_per_font,
        ),
        "directius_sector_public": socrata.query(
            "retrib_directius_sector_public",
            where=f"upper(cognoms_i_nom) like upper('%{nom}%')",
            order="retribuci_fixa_anual_prevista DESC",
            limit=limit_per_font,
        ),
        "declaracions_activitats": socrata.query(
            "declaracions_activitats",
            where=(
                f"(upper(nom) like upper('%{nom}%') OR "
                f"upper(primer_cognom) like upper('%{nom}%'))"
            ),
            limit=limit_per_font,
        ),
        "viatges": socrata.query(
            "viatges_alts_carrecs",
            where=f"upper(nom_i_cognoms) like upper('%{nom}%')",
            order="inici_viatge DESC",
            limit=limit_per_font,
        ),
    }

    settled = await asyncio.gather(
        *queries.values(), return_exceptions=True
    )

    for key, result in zip(queries.keys(), settled):
        if isinstance(result, Exception):
            results[key] = []
        else:
            results[key] = result

    # Corregir imports de contractes menors (venen en cèntims)
    if results.get("contractes_menors"):
        _fix_import_centims(results["contractes_menors"], "import_adjudicat_sense_iva")

    # Construir informe
    sections = []
    sections.append(f"# INFORME D'INVESTIGACIÓ: {nom.upper()}\n")

    total_aparicions = 0
    for key, records in results.items():
        count = len(records)
        total_aparicions += count
        if count > 0:
            sections.append(f"\n## {key.upper().replace('_', ' ')} ({count} resultats)")
            sections.append(json.dumps(records, ensure_ascii=False, indent=2))

    if total_aparicions == 0:
        sections.append("\nNo s'han trobat resultats a cap font de dades.")
    else:
        sections.insert(1, f"\nTotal aparicions: {total_aparicions} a {sum(1 for r in results.values() if r)} fonts de dades.\n")

    return "\n".join(sections)


@mcp.tool()
async def detectar_concentracio_contractes(
    departament: Annotated[str | None, Field(description="Nom del departament a analitzar (opcional, tots si no s'indica)")] = None,
    any: Annotated[str | None, Field(description="Any a analitzar (ex: '2024')")] = None,
    limit: Annotated[int, Field(description="Top N empreses a mostrar")] = 50,
) -> str:
    """Detecta concentració anòmala de contractes en poques empreses.

    Mostra les empreses que acumulen més contractes i import total
    en un departament o any. Útil per detectar possibles favoritismes.

    Retorna: empresa, nombre de contractes, import total.
    """
    clauses = []
    if departament:
        clauses.append(f"upper(organisme_contractant) like upper('%{departament}%')")
    if any:
        clauses.append(f"exercici='{any}'")

    where = _build_where(clauses)

    # Nombre de contractes per empresa
    count_records, total = await socrata.query_with_count(
        "contractes",
        select="adjudicatari, count(*) as num_contractes, sum(import_adjudicacio) as import_total",
        where=where,
        group="adjudicatari",
        order="num_contractes DESC",
        limit=limit,
    )

    if not count_records:
        return "No s'han trobat resultats."

    lines = ["# ANÀLISI DE CONCENTRACIÓ DE CONTRACTES\n"]
    if departament:
        lines.append(f"Departament/Organisme: {departament}")
    if any:
        lines.append(f"Any: {any}")
    lines.append(f"Top {limit} empreses per nombre de contractes:\n")
    lines.append(json.dumps(count_records, ensure_ascii=False, indent=2))

    return "\n".join(lines)


@mcp.tool()
async def detectar_fraccionament(
    empresa: Annotated[str, Field(description="Nom de l'empresa a analitzar")],
    exercici: Annotated[str | None, Field(description="Any a analitzar (ex: '2024')")] = None,
) -> str:
    """Detecta possible fraccionament de contractes menors d'una empresa.

    El fraccionament consisteix en dividir un contracte gran en diversos
    contractes menors per evitar la licitació pública (límit: 15.000€ serveis,
    40.000€ obres).

    Analitza: nombre de contractes menors, imports, departaments, i si
    hi ha patrons temporals sospitosos.
    """
    clauses = [f"upper(empresa_adjudicat_ria) like upper('%{empresa}%')"]
    if exercici:
        clauses.append(f"any='{exercici}'")

    # Obtenir tots els contractes menors de l'empresa
    records, total = await socrata.query_with_count(
        "contractes_menors",
        where=_build_where(clauses),
        order="import_adjudicat_sense_iva DESC",
        limit=200,
    )

    if not records:
        return f"No s'han trobat contractes menors per '{empresa}'."

    _fix_import_centims(records, "import_adjudicat_sense_iva")

    # Analitzar
    total = len(records)
    imports = []
    departaments: dict[str, int] = {}
    for r in records:
        try:
            imp = float(r.get("import_adjudicat_sense_iva", 0))
            imports.append(imp)
        except (ValueError, TypeError):
            pass
        dept = r.get("departament_d_adscripci", "Desconegut")
        departaments[dept] = departaments.get(dept, 0) + 1

    import_total = sum(imports)
    import_mitja = import_total / len(imports) if imports else 0
    import_max = max(imports) if imports else 0

    has_alerts = False
    analitzats = len(records)
    total_real = total if total is not None else analitzats
    lines = [f"# ANÀLISI DE FRACCIONAMENT: {empresa.upper()}\n"]
    if exercici:
        lines.append(f"Any: {exercici}")
    lines.append(f"Total contractes menors trobats: {total_real}")
    if total_real > analitzats:
        lines.append(f"Analitzats: {analitzats} de {total_real} (augmenta el limit per analitzar-los tots)")
    lines.append(f"Import total acumulat: {import_total:,.2f} €")
    lines.append(f"Import mitjà per contracte: {import_mitja:,.2f} €")
    lines.append(f"Import màxim: {import_max:,.2f} €")
    lines.append(f"\nDistribució per departament:")
    for dept, count in sorted(departaments.items(), key=lambda x: -x[1]):
        lines.append(f"  - {dept}: {count} contractes")

    # Alertes
    lines.append("\n## INDICADORS DE RISC:")
    if total >= 5 and import_total > 40000:
        has_alerts = True
        lines.append("⚠ ALERTA: Acumulació significativa de contractes menors "
                      f"({total} contractes, {import_total:,.2f} € total). "
                      "Possible fraccionament per evitar licitació.")
    if import_mitja > 10000:
        has_alerts = True
        lines.append("⚠ ALERTA: Import mitjà elevat per a contractes menors "
                      f"({import_mitja:,.2f} €). Prop del límit legal.")
    if len(departaments) == 1 and total >= 3:
        has_alerts = True
        dept_unic = list(departaments.keys())[0]
        lines.append(f"⚠ ALERTA: Tots els contractes provenen del mateix departament "
                      f"({dept_unic}). Possible relació de dependència.")
    if not has_alerts:
        lines.append("✓ No s'han detectat indicadors de risc evidents.")

    lines.append("\n## DETALL DELS CONTRACTES:")
    lines.append(json.dumps(records[:20], ensure_ascii=False, indent=2))
    if total > 20:
        lines.append(f"\n... i {total - 20} contractes més.")

    return "\n".join(lines)


# ===========================================================================
# datos.gob.es — Catàleg nacional de dades obertes
# ===========================================================================


@mcp.tool()
async def datosgob_cercar_datasets(
    query: Annotated[str | None, Field(description="Text lliure per cercar (ex: 'contratos públicos', 'presupuestos')")] = None,
    theme: Annotated[str | None, Field(description="Temàtica: 'sector-publico', 'economia', 'hacienda', 'empleo', 'medio-ambiente', 'salud', 'educacion', 'transporte'")] = None,
    publisher: Annotated[str | None, Field(description="Organisme publicador (ex: 'Ministerio de Hacienda')")] = None,
    format_: Annotated[str | None, Field(description="Format dels recursos: 'json', 'csv', 'api', 'xml'")] = None,
    page_size: Annotated[int, Field(description="Resultats per pàgina (per defecte 20)")] = 20,
    page: Annotated[int, Field(description="Pàgina (0-indexed)")] = 0,
) -> str:
    """Cerca datasets al catàleg nacional de dades obertes datos.gob.es.

    Permet trobar datasets publicats per administracions espanyoles sobre
    contractació, pressupostos, economia, sector públic i molt més.
    Hi ha 113.000+ datasets disponibles.
    """
    result = await datosgob.buscar_datasets(
        query=query,
        theme=theme,
        publisher=publisher,
        format_=format_,
        page_size=page_size,
        page=page,
    )
    items = result.get("result", {}).get("items", [])
    if not items:
        return "No s'han trobat datasets."

    total_str = ""
    total_results = result.get("result", {}).get("totalResults")
    if total_results:
        total_str = f"Total: {total_results} datasets trobats.\n\n"

    records = []
    for item in items:
        title = item.get("title", "")
        if isinstance(title, list):
            title = title[0] if title else ""
        elif isinstance(title, dict):
            title = title.get("_value", title.get("es", str(title)))
        desc = item.get("description", "")
        if isinstance(desc, list):
            desc = desc[0] if desc else ""
        elif isinstance(desc, dict):
            desc = desc.get("_value", desc.get("es", str(desc)))
        records.append({
            "titol": title,
            "descripcio": str(desc)[:200],
            "id": item.get("identifier", ""),
            "publicador": item.get("publisher", ""),
            "modificat": item.get("modified", ""),
            "llicencia": item.get("license", ""),
        })

    return total_str + json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def datosgob_detall_dataset(
    dataset_id: Annotated[str, Field(description="Identificador del dataset (obtingut via datosgob_cercar_datasets)")],
) -> str:
    """Obté el detall complet d'un dataset de datos.gob.es.

    Inclou distribucions (fitxers descarregables, APIs), metadades,
    freqüència d'actualització i recursos disponibles.
    """
    result = await datosgob.detall_dataset(dataset_id)
    items = result.get("result", {}).get("items", [])
    if not items:
        return f"No s'ha trobat el dataset amb id '{dataset_id}'."
    return json.dumps(items[0], ensure_ascii=False, indent=2)


# ===========================================================================
# CGPJ — Consejo General del Poder Judicial
# ===========================================================================


@mcp.tool()
async def cgpj_dades_corrupcio() -> str:
    """Obté dades del repositori de processos per corrupció del CGPJ.

    El CGPJ publica un repositori específic amb informació sobre
    macrocauses, procediments a l'Audiència Nacional i als tribunals
    superiors de justícia relacionats amb corrupció política i econòmica.
    """
    result = await cgpj.obtenir_dades_corrupcio()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def cgpj_cercar_sentencies(
    text: Annotated[str | None, Field(description="Text lliure per cercar a les resolucions (ex: 'malversación', 'cohecho', 'prevaricación')")] = None,
    organ: Annotated[str | None, Field(description="Tipus d'òrgan: 'TS' (Tribunal Suprem), 'AN' (Audiència Nacional), 'AP' (Audiència Provincial)")] = None,
    tipus: Annotated[str | None, Field(description="Tipus de resolució: 'SENTENCIA', 'AUTO'")] = None,
    data_desde: Annotated[str | None, Field(description="Data inici DD/MM/YYYY")] = None,
    data_fins: Annotated[str | None, Field(description="Data fi DD/MM/YYYY")] = None,
    page: Annotated[int, Field(description="Pàgina de resultats")] = 1,
    page_size: Annotated[int, Field(description="Resultats per pàgina")] = 20,
) -> str:
    """Cerca sentències al CENDOJ (Centre de Documentació Judicial).

    Permet cercar resolucions judicials per text, òrgan judicial, tipus
    i dates. Molt útil per trobar sentències de corrupció, malversació,
    prevaricació, suborn i altres delictes contra l'administració pública.
    """
    result = await cgpj.cercar_sentencies(
        text=text,
        organ=organ,
        tipus=tipus,
        data_desde=data_desde,
        data_fins=data_fins,
        page=page,
        page_size=page_size,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def cgpj_estadistiques_judicials(
    tema: Annotated[str | None, Field(description="Tema: 'penal', 'civil', 'contencioso', 'social', 'menores'")] = None,
    territori: Annotated[str | None, Field(description="Àmbit territorial (ex: 'nacional', 'Madrid', 'Barcelona', 'Cataluña')")] = None,
    any_: Annotated[str | None, Field(description="Any de les estadístiques (ex: '2024')")] = None,
) -> str:
    """Consulta estadístiques judicials del CGPJ.

    Dades agregades sobre activitat judicial per tema, territori i any.
    Inclou volum de procediments, durada, taxes de resolució, etc.
    """
    result = await cgpj.buscar_estadistiques_judicials(
        tema=tema,
        territori=territori,
        any_=any_,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ===========================================================================
# Open Data BCN — Ajuntament de Barcelona (API CKAN)
# ===========================================================================


@mcp.tool()
async def bcn_cercar_datasets(
    query: Annotated[str | None, Field(description="Text lliure per cercar (ex: 'pressupost', 'seguretat', 'habitatge')")] = None,
    rows: Annotated[int, Field(description="Nombre de resultats (per defecte 20)")] = 20,
    start: Annotated[int, Field(description="Offset per paginació")] = 0,
) -> str:
    """Cerca datasets a l'Open Data de l'Ajuntament de Barcelona.

    553 datasets municipals sobre: pressupostos, contractes, seguretat
    (incidents Guàrdia Urbana), transport (bicing, bus, taxi), medi ambient
    (qualitat aire, espais verds), habitatge, urbanisme i economia.
    """
    result = await barcelona.cercar_datasets(query=query, rows=rows, start=start)
    if not result.get("success"):
        return "Error en la consulta a Open Data BCN."

    results = result.get("result", {})
    count = results.get("count", 0)
    datasets = results.get("results", [])

    if not datasets:
        return "No s'han trobat datasets a Barcelona."

    records = []
    for ds in datasets:
        records.append({
            "nom": ds.get("title", ""),
            "id": ds.get("name", ""),
            "descripcio": (ds.get("notes_translated", {}).get("ca", "") or ds.get("notes", ""))[:200],
            "num_recursos": ds.get("num_resources", 0),
            "etiquetes": [t.get("name", "") for t in ds.get("tags", [])],
        })

    header = f"Total: {count} datasets trobats.\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def bcn_detall_dataset(
    dataset_name: Annotated[str, Field(description=(
        "Nom del dataset. Exemples: 'pressupost-despeses', 'pressupost-ingressos', "
        "'contractes-menors', 'incidents-gestionats-gub', 'qualitat-aire-detall-bcn', "
        "'habitatges-us-turistic', 'bicing', 'obres', 'renda-disponible-llars-bcn'"
    ))],
) -> str:
    """Obté el detall complet d'un dataset de Barcelona, incloent els seus recursos.

    Retorna metadades i la llista de recursos (fitxers CSV, JSON, etc.)
    amb els seus resource_id per poder consultar-los amb bcn_obtenir_dades.
    """
    result = await barcelona.detall_dataset(dataset_name)
    if not result.get("success"):
        return f"No s'ha trobat el dataset '{dataset_name}'."

    ds = result.get("result", {})
    resources = []
    for r in ds.get("resources", []):
        resources.append({
            "id": r.get("id", ""),
            "nom": r.get("name", ""),
            "format": r.get("format", ""),
            "url": r.get("url", ""),
        })

    info = {
        "nom": ds.get("title", ""),
        "descripcio": ds.get("notes_translated", {}).get("ca", "") or ds.get("notes", ""),
        "llicencia": ds.get("license_title", ""),
        "recursos": resources,
    }
    return json.dumps(info, ensure_ascii=False, indent=2)


@mcp.tool()
async def bcn_obtenir_dades(
    resource_id: Annotated[str, Field(description="ID del recurs (obtingut via bcn_detall_dataset)")],
    query: Annotated[str | None, Field(description="Text lliure per filtrar les dades")] = None,
    limit: Annotated[int, Field(description="Nombre de resultats (per defecte 20)")] = 20,
    offset: Annotated[int, Field(description="Offset per paginació")] = 0,
) -> str:
    """Obté dades d'un recurs concret de Barcelona via l'API datastore.

    Primer usa bcn_detall_dataset per obtenir els resource_id disponibles,
    després aquesta tool per consultar les dades reals.
    """
    result = await barcelona.obtenir_dades(
        resource_id, query=query, limit=limit, offset=offset,
    )
    if not result.get("success"):
        return "Error obtenint dades del recurs."

    data = result.get("result", {})
    records = data.get("records", [])
    total = data.get("total", 0)

    if not records:
        return "No s'han trobat registres."

    header = ""
    if total:
        shown = len(records)
        header = f"Mostrant {offset + 1}-{offset + shown} de {total} registres.\n\n"

    return header + json.dumps(records, ensure_ascii=False, indent=2)


# ===========================================================================
# BOE — Boletín Oficial del Estado
# ===========================================================================


def _normalitza_items(items) -> list:
    """Normalitza items del BOE que poden ser dict o list."""
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


def _extreure_items_seccio(sumari: dict, codi_seccio: str) -> list[dict]:
    """Extreu tots els items d'una secció del sumari del BOE."""
    resultats = []
    for diario in _normalitza_items(sumari.get("data", {}).get("sumario", {}).get("diario", [])):
        for seccion in _normalitza_items(diario.get("seccion", [])):
            if seccion.get("codigo") != codi_seccio:
                continue
            for dept in _normalitza_items(seccion.get("departamento", [])):
                dept_nom = dept.get("nombre", "")
                epigrafe_raw = dept.get("epigrafe", dept.get("texto", []))
                for ep in _normalitza_items(epigrafe_raw):
                    ep_nom = ep.get("nombre", "")
                    for item in _normalitza_items(ep.get("item", [])):
                        url_pdf = item.get("url_pdf", {})
                        if isinstance(url_pdf, dict):
                            url_pdf = url_pdf.get("texto", "")
                        resultats.append({
                            "departament": dept_nom,
                            "epigrafe": ep_nom,
                            "identificador": item.get("identificador", ""),
                            "titol": item.get("titulo", ""),
                            "url_html": item.get("url_html", ""),
                            "url_pdf": url_pdf,
                        })
    return resultats


@mcp.tool()
async def boe_sumari(
    data: Annotated[str, Field(description=(
        "Data del sumari en format YYYYMMDD (ex: '20260314'). "
        "Si no se sap la data exacta, provar amb dies laborables recents."
    ))],
    seccio: Annotated[str | None, Field(description=(
        "Filtrar per secció. Codis: "
        "'1' = Disposicions generals, "
        "'2A' = Nomenaments i cessaments, "
        "'2B' = Oposicions i concursos, "
        "'3' = Altres disposicions, "
        "'4' = Administració de Justícia, "
        "'5A' = Contractació del Sector Públic, "
        "'5B' = Altres anuncis oficials, "
        "'5C' = Anuncis particulars. "
        "Si no s'especifica, retorna totes les seccions."
    ))] = None,
    departament: Annotated[str | None, Field(description=(
        "Filtrar per departament (text parcial, case-insensitive). "
        "Ex: 'Defensa', 'Hacienda', 'Interior'"
    ))] = None,
) -> str:
    """Consulta el sumari diari del BOE (Boletín Oficial del Estado).

    Retorna els documents publicats al BOE per una data concreta.
    Molt útil per trobar nomenaments i cessaments (secció 2A),
    contractes públics (secció 5A), i disposicions generals (secció 1).

    Per detectar PORTES GIRATÒRIES: cerca nomenaments/cessaments a la
    secció 2A i creua amb cercar_contractes o cercar_subvencions.
    """
    try:
        result = await boe.obtenir_sumari(data)
    except Exception:
        return f"Error consultant el BOE per la data {data}. Comprova que la data sigui vàlida (format YYYYMMDD) i correspongui a un dia amb publicació."

    if result.get("status", {}).get("code") != "200":
        return f"Error consultant el BOE per la data {data}."

    if seccio:
        items = _extreure_items_seccio(result, seccio)
    else:
        items = []
        for codi in ["1", "2A", "2B", "3", "4", "5A", "5B", "5C"]:
            items.extend(_extreure_items_seccio(result, codi))

    if departament:
        dept_lower = departament.lower()
        items = [i for i in items if dept_lower in i.get("departament", "").lower()]

    if not items:
        filtres = f"data={data}"
        if seccio:
            filtres += f", seccio={seccio}"
        if departament:
            filtres += f", departament={departament}"
        return f"No s'han trobat resultats al BOE ({filtres})."

    total = len(items)
    shown = items[:50]
    header = f"Total: {total} documents trobats al BOE del {data}.\n\n"
    return header + json.dumps(shown, ensure_ascii=False, indent=2)


@mcp.tool()
async def boe_nomenaments(
    data: Annotated[str, Field(description="Data en format YYYYMMDD (ex: '20260314')")],
    departament: Annotated[str | None, Field(description=(
        "Filtrar per departament (text parcial). Ex: 'Defensa', 'Interior'"
    ))] = None,
) -> str:
    """Cerca nomenaments, cessaments i situacions de personal al BOE.

    Extreu específicament la secció 2A del BOE (Nombramientos, situaciones
    e incidencias). Útil per detectar portes giratòries creuant amb
    contractes i subvencions.
    """
    try:
        result = await boe.obtenir_sumari(data)
    except Exception:
        return f"Error consultant el BOE per la data {data}. Comprova que la data sigui vàlida."

    if result.get("status", {}).get("code") != "200":
        return f"Error consultant el BOE per la data {data}."

    items = _extreure_items_seccio(result, "2A")

    if departament:
        dept_lower = departament.lower()
        items = [i for i in items if dept_lower in i.get("departament", "").lower()]

    if not items:
        return f"No s'han trobat nomenaments al BOE del {data}."

    total = len(items)
    header = f"Total: {total} nomenaments/cessaments al BOE del {data}.\n\n"
    return header + json.dumps(items[:50], ensure_ascii=False, indent=2)


@mcp.tool()
async def boe_contractes(
    data: Annotated[str, Field(description="Data en format YYYYMMDD (ex: '20260314')")],
    departament: Annotated[str | None, Field(description=(
        "Filtrar per departament (text parcial). Ex: 'Defensa', 'Sanidad'"
    ))] = None,
) -> str:
    """Cerca anuncis de contractació del sector públic publicats al BOE.

    Extreu la secció 5A del BOE (Contratación del Sector Público).
    Inclou licitacions i adjudicacions publicades oficialment.
    """
    try:
        result = await boe.obtenir_sumari(data)
    except Exception:
        return f"Error consultant el BOE per la data {data}. Comprova que la data sigui vàlida."

    if result.get("status", {}).get("code") != "200":
        return f"Error consultant el BOE per la data {data}."

    items = _extreure_items_seccio(result, "5A")

    if departament:
        dept_lower = departament.lower()
        items = [i for i in items if dept_lower in i.get("departament", "").lower()]

    if not items:
        return f"No s'han trobat contractes al BOE del {data}."

    total = len(items)
    header = f"Total: {total} anuncis de contractació al BOE del {data}.\n\n"
    return header + json.dumps(items[:50], ensure_ascii=False, indent=2)


@mcp.tool()
async def boe_legislacio(
    limit: Annotated[int, Field(description="Nombre de resultats (per defecte 20)")] = 20,
    offset: Annotated[int, Field(description="Offset per paginació")] = 0,
) -> str:
    """Consulta legislació consolidada d'Espanya via el BOE.

    Retorna les normes més recentment actualitzades amb informació
    sobre àmbit (estatal, autonòmic), rang (llei, decret, ordre),
    departament i estat de consolidació.
    """
    result = await boe.cercar_legislacio(limit=limit, offset=offset)

    if result.get("status", {}).get("code") != "200":
        return "Error consultant la legislació consolidada del BOE."

    data = result.get("data", [])
    if not data:
        return "No s'han trobat resultats de legislació."

    records = []
    for item in data:
        records.append({
            "identificador": item.get("identificador", ""),
            "titol": item.get("titulo", ""),
            "rang": item.get("rango", {}).get("texto", ""),
            "departament": item.get("departamento", {}).get("texto", ""),
            "ambit": item.get("ambito", {}).get("texto", ""),
            "data_disposicio": item.get("fecha_disposicion", ""),
            "data_publicacio": item.get("fecha_publicacion", ""),
            "vigencia_agotada": item.get("vigencia_agotada", ""),
            "estat_consolidacio": item.get("estado_consolidacion", {}).get("texto", ""),
            "url": item.get("url_html_consolidada", ""),
        })

    total = len(records)
    header = f"Mostrant {total} normes de legislació consolidada.\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def boe_departaments() -> str:
    """Llista tots els departaments disponibles al BOE.

    Útil per saber quins codis i noms de departament es poden usar
    per filtrar en altres consultes al BOE.
    """
    result = await boe.obtenir_departaments()

    if result.get("status", {}).get("code") != "200":
        return "Error obtenint els departaments del BOE."

    data = result.get("data", {})
    records = [{"codi": k, "nom": v} for k, v in sorted(data.items(), key=lambda x: x[1])]
    return json.dumps(records, ensure_ascii=False, indent=2)


# ===========================================================================
# BORME — Boletín Oficial del Registro Mercantil
# ===========================================================================


@mcp.tool()
async def borme_sumari(
    data: Annotated[str, Field(description="Data en format YYYYMMDD (ex: '20260314')")],
    provincia: Annotated[str | None, Field(description=(
        "Filtrar per província (text parcial). Ex: 'Barcelona', 'Madrid', 'Valencia'"
    ))] = None,
) -> str:
    """Consulta el sumari diari del BORME (Registre Mercantil).

    Retorna els actes inscrits d'empreses per província: constitucions,
    nomenaments d'administradors, cessaments, dissolucions, canvis d'objecte
    social, ampliacions de capital, etc.

    Cada entrada inclou un PDF amb els detalls de les inscripcions.
    Útil per investigar activitat societària i creuar amb contractes públics.
    """
    try:
        result = await boe.obtenir_sumari_borme(data)
    except Exception:
        return f"Error consultant el BORME per la data {data}. Comprova que sigui vàlida (YYYYMMDD) i dia laborable."

    if result.get("status", {}).get("code") != "200":
        return f"Error consultant el BORME per la data {data}."

    items = []
    for diario in _normalitza_items(result.get("data", {}).get("sumario", {}).get("diario", [])):
        for seccion in _normalitza_items(diario.get("seccion", [])):
            for item in _normalitza_items(seccion.get("item", [])):
                url_pdf = item.get("url_pdf", {})
                if isinstance(url_pdf, dict):
                    url_pdf = url_pdf.get("texto", "")
                items.append({
                    "seccio": seccion.get("nombre", ""),
                    "provincia": item.get("titulo", ""),
                    "identificador": item.get("identificador", ""),
                    "url_pdf": url_pdf,
                })

    if provincia:
        prov_lower = provincia.lower()
        items = [i for i in items if prov_lower in i.get("provincia", "").lower()]

    if not items:
        return f"No s'han trobat actes al BORME del {data}."

    total = len(items)
    header = f"Total: {total} publicacions al BORME del {data}.\n\n"
    return header + json.dumps(items[:50], ensure_ascii=False, indent=2)


# ===========================================================================
# INE — Instituto Nacional de Estadística
# ===========================================================================


@mcp.tool()
async def ine_operacions(
    query: Annotated[str | None, Field(description=(
        "Text per filtrar operacions (ex: 'IPC', 'empleo', 'población', 'PIB')"
    ))] = None,
) -> str:
    """Llista les operacions estadístiques disponibles a l'INE.

    Hi ha 111 operacions: IPC, EPA (enquesta de població activa),
    PIB, demografia, cens, turisme, etc. Usa aquesta tool primer
    per trobar el codi d'operació, i després ine_taules per veure
    les taules disponibles.
    """
    try:
        ops = await ine.llistar_operacions()
    except Exception:
        return "Error consultant l'INE."

    if query:
        q_lower = query.lower()
        ops = [o for o in ops if q_lower in json.dumps(o, ensure_ascii=False).lower()]

    if not ops:
        return "No s'han trobat operacions."

    records = []
    for op in ops[:50]:
        records.append({
            "id": op.get("Id", op.get("id", "")),
            "codi": op.get("Cod_IOE", op.get("cod_IOE", "")),
            "nom": op.get("Nombre", op.get("nombre", "")),
        })

    header = f"Total: {len(ops)} operacions trobades.\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def ine_taules(
    operacio: Annotated[str, Field(description=(
        "Codi de l'operació (ex: 'IPC', 'EPA', 'ECV', 'PIB'). "
        "Obtingut via ine_operacions."
    ))],
) -> str:
    """Llista les taules disponibles d'una operació estadística de l'INE.

    Retorna els IDs de taula necessaris per consultar dades amb ine_dades_taula.
    """
    try:
        taules = await ine.llistar_taules(operacio)
    except Exception:
        return f"Error consultant les taules de l'operació '{operacio}'."

    if not taules:
        return f"No s'han trobat taules per l'operació '{operacio}'."

    records = []
    for t in taules[:50]:
        records.append({
            "id": t.get("Id", t.get("id", "")),
            "nom": t.get("Nombre", t.get("nombre", "")),
        })

    header = f"Total: {len(taules)} taules per '{operacio}'.\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def ine_dades_taula(
    taula_id: Annotated[int, Field(description="ID numèric de la taula (obtingut via ine_taules)")],
    nult: Annotated[int, Field(description="Nombre d'últims períodes a retornar (per defecte 5)")] = 5,
) -> str:
    """Obté les dades d'una taula estadística de l'INE.

    Retorna els valors dels últims períodes per a la taula indicada.
    Inclou IPC, atur, població, renda, PIB i molts altres indicadors.
    """
    try:
        dades = await ine.obtenir_dades_taula(taula_id, nult=nult)
    except Exception:
        return f"Error obtenint dades de la taula {taula_id}."

    if not dades:
        return f"No s'han trobat dades per la taula {taula_id}."

    return json.dumps(dades, ensure_ascii=False, indent=2)


@mcp.tool()
async def ine_serie(
    serie: Annotated[str, Field(description="Codi de la sèrie (ex: 'IPC206449')")],
    nult: Annotated[int, Field(description="Nombre d'últims períodes (per defecte 10)")] = 10,
) -> str:
    """Obté una sèrie temporal concreta de l'INE.

    Útil quan es coneix el codi de sèrie exacte.
    """
    try:
        dades = await ine.obtenir_serie(serie, nult=nult)
    except Exception:
        return f"Error obtenint la sèrie '{serie}'."

    if not dades:
        return f"No s'han trobat dades per la sèrie '{serie}'."

    return json.dumps(dades, ensure_ascii=False, indent=2)


# ===========================================================================
# BdE — Banc d'Espanya
# ===========================================================================


@mcp.tool()
async def bde_serie(
    series: Annotated[str, Field(description=(
        "Codis de sèries separats per comes. Exemples: "
        "'D_1NBAF472' (Euribor 1 any), "
        "'D_1NBAF474' (Euribor 3 mesos), "
        "'D_1AEA8S1' (IPC general), "
        "'D_1BE9994' (Deute públic), "
        "'D_1NBAF468' (Tipus interès BCE)"
    ))],
) -> str:
    """Obté l'últim valor de sèries financeres del Banc d'Espanya.

    Inclou Euribor, IPC, deute públic, tipus d'interès del BCE, etc.
    Per contextualitzar investigacions amb dades macroeconòmiques.
    """
    try:
        result = await bde.obtenir_ultim_valor(series)
    except Exception:
        return f"Error consultant el Banc d'Espanya per les sèries '{series}'."

    if not result:
        return "No s'han trobat dades."

    records = []
    for item in result if isinstance(result, list) else [result]:
        records.append({
            "serie": item.get("serie", ""),
            "descripcio": item.get("descripcionCorta", ""),
            "valor": item.get("valor"),
            "data": item.get("fechaValor", ""),
            "unitat": item.get("simbolo", ""),
            "frequencia": item.get("codFrecuencia", ""),
        })

    return json.dumps(records, ensure_ascii=False, indent=2)


@mcp.tool()
async def bde_series_destacades() -> str:
    """Mostra les sèries financeres més destacades del Banc d'Espanya.

    Retorna l'últim valor de: Euribor (1 any, 3 i 6 mesos),
    tipus d'interès del BCE, IPC general i deute públic.
    """
    codis = ",".join(bde.SERIES_DESTACADES.values())
    try:
        result = await bde.obtenir_ultim_valor(codis)
    except Exception:
        return "Error consultant el Banc d'Espanya."

    if not result:
        return "No s'han trobat dades."

    records = []
    for item in result if isinstance(result, list) else [result]:
        records.append({
            "serie": item.get("serie", ""),
            "descripcio": item.get("descripcionCorta", ""),
            "valor": item.get("valor"),
            "data": item.get("fechaValor", ""),
            "unitat": item.get("simbolo", ""),
        })

    return json.dumps(records, ensure_ascii=False, indent=2)


# ===========================================================================
# PGE — Pressupostos Generals de l'Estat
# ===========================================================================


@mcp.tool()
async def pge_estructura(
    any_: Annotated[int, Field(description=(
        "Any dels pressupostos (2015-2025). Ex: 2024"
    ))] = 2024,
) -> str:
    """Obté l'estructura dels Pressupostos Generals de l'Estat.

    Retorna l'arbre de seccions (ministeris), subsectors i programes
    pressupostaris amb enllaços als fitxers CSV/XML/PDF de detall.
    Disponible des de 2015 fins a 2025.
    """
    if any_ not in pge.ANYS_DISPONIBLES:
        return f"Any {any_} no disponible. Anys vàlids: {pge.ANYS_DISPONIBLES}"

    try:
        index = await pge.obtenir_index(any_)
    except Exception:
        return f"Error obtenint els PGE de l'any {any_}."

    # Extreure seccions (ministeris) — l'XML té 2 nivells: Gastos > SAL > Seccions
    estructura = index.get("Estructura", {})
    sector = estructura.get("Estructura", {})
    if isinstance(sector, dict):
        seccions_raw = sector.get("Estructura", [])
    else:
        seccions_raw = sector
    if isinstance(seccions_raw, dict):
        seccions_raw = [seccions_raw]

    records = []
    for seccio in seccions_raw:
        subsectors = seccio.get("Estructura", [])
        if isinstance(subsectors, dict):
            subsectors = [subsectors]

        # Collect CSV links
        csv_links = []
        for sub in subsectors:
            informe = sub.get("Informe", {})
            if isinstance(informe, dict):
                for enllac in _normalitza_items(informe.get("Enlace", [])):
                    url = enllac.get("url", "")
                    if url.endswith(".CSV") or url.endswith(".csv"):
                        csv_links.append(url)

        records.append({
            "codi": seccio.get("codigo", ""),
            "nom": seccio.get("literal", ""),
            "subsectors": len(subsectors),
            "csv_disponibles": len(csv_links),
        })

    header = f"PGE {any_}: {len(records)} seccions (ministeris).\n\n"
    return header + json.dumps(records, ensure_ascii=False, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

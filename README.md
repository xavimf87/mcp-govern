# mcp-govern

Servidor MCP (Model Context Protocol) expert en **transparencia publica** i **deteccio de patrons de corrupcio** a partir de dades obertes del **Govern de Catalunya**, l'**Ajuntament de Barcelona** i fonts de dades de tota **Espanya**.

Contractes, subvencions, sous, pressupostos, lobbies, viatges, sentencies judicials — 34 tools que creuen automaticament 45+ datasets per trobar anomalies, fraccionaments i conflictes d'interes.

## Que es un MCP?

Un MCP (Model Context Protocol) es un servidor que dona "superpoderes" a Claude (o altres LLMs). En aquest cas, permet que Claude consulti en temps real les bases de dades publiques del Govern de Catalunya, l'Ajuntament de Barcelona i d'Espanya. Tu preguntes en llenguatge natural i Claude fa les consultes per tu.

Per exemple:
- *"Investiga Telefonica: contractes, subvencions, reunions amb lobbies"* → Claude creua 10 bases de dades en paral·lel
- *"Quant cobra el president de la Generalitat?"* → Claude consulta les taules retributives oficials
- *"Quines empreses acaparen els contractes menors de Salut?"* → Claude detecta concentracio sospitosa
- *"Busca sentencies de corrupcio a l'Audiencia Nacional"* → Claude cerca al CENDOJ
- *"Quin es el pressupost de despeses de Barcelona?"* → Claude consulta l'Open Data BCN

**No necessites saber programar.** Nomes cal instal·lar-lo i preguntar.

## Fonts de dades

| Font | Abast | API |
|---|---|---|
| [analisi.transparenciacatalunya.cat](https://analisi.transparenciacatalunya.cat) | Catalunya | Socrata (SODA) |
| [BDNS](https://www.pap.hacienda.gob.es/bdnstrans/) | Espanya | REST |
| [datos.gob.es](https://datos.gob.es) | Espanya | CKAN |
| [CGPJ](https://www.poderjudicial.es) | Espanya | REST / PC-Axis |
| [Open Data BCN](https://opendata-ajuntament.barcelona.cat) | Barcelona | CKAN |

No requereix autenticacio ni API keys. Totes les dades son publiques.

## Guia d'instal·lacio pas a pas

### Requisits previs

Nomes necessites dues coses:

1. **Claude Code** o **Claude Desktop** — L'aplicacio de Claude que fara servir el MCP.
   - Claude Code: [claude.com/claude-code](https://claude.com/claude-code)
   - Claude Desktop: [claude.ai/download](https://claude.ai/download)

2. **uv** — Gestor de paquets de Python. Si no el tens, instal·la'l amb:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Pas 1: Descarregar el projecte

Obre un terminal i executa:

```bash
git clone https://github.com/xavidop/mcp-govern.git
cd mcp-govern
uv sync
```

Aixo descarrega el codi i instal·la totes les dependencies automaticament.

### Pas 2: Connectar amb Claude

Tria la opcio que facis servir:

#### Opcio A: Claude Code (recomanat)

Executa aquesta comanda dins de Claude Code:

```
/mcp add govern -- uv run --directory /ruta/a/mcp-govern mcp-govern
```

Substitueix `/ruta/a/mcp-govern` per la ruta real on has descarregat el projecte. Per exemple:
- macOS: `/Users/elteunomdusuari/mcp-govern`
- Linux: `/home/elteunomdusuari/mcp-govern`
- Windows: `C:\Users\elteunomdusuari\mcp-govern`

Per verificar que funciona, executa `/mcp` a Claude Code i comprova que `govern` apareix com a `connected`.

#### Opcio B: Claude Desktop

1. Obre Claude Desktop
2. Ves a **Settings** → **Developer** → **Edit Config**
3. Afegeix dins de `mcpServers`:

```json
{
  "mcpServers": {
    "govern": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/a/mcp-govern", "mcp-govern"]
    }
  }
}
```

4. Reinicia Claude Desktop

#### Opcio C: Configuracio manual (avancada)

Si prefereixes editar els fitxers de configuracio directament:

**Claude Code global** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "govern": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/a/mcp-govern", "mcp-govern"]
    }
  }
}
```

**Claude Code per projecte** (`.mcp.json` a l'arrel del projecte):
```json
{
  "mcpServers": {
    "govern": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/a/mcp-govern", "mcp-govern"]
    }
  }
}
```

### Pas 3: Comprovar que funciona

Obre Claude i pregunta:

> Quant cobra el president de la Generalitat?

Si veus que Claude fa una crida a `govern - cercar_retribucions_alts_carrecs` i retorna el sou, tot funciona correctament.

### Resolucio de problemes

| Problema | Solucio |
|---|---|
| `govern` no apareix a `/mcp` | Comprova que la ruta al projecte es correcta. Reinicia Claude. |
| Error `uv: command not found` | Instal·la `uv` (veure requisits previs). Si l'acabes d'instal·lar, reinicia el terminal. |
| Error de connexio | Les APIs publiques poden estar temporalment caigudes. Torna-ho a provar mes tard. |
| `govern` apareix com `error` | Executa `uv run --directory /ruta/a/mcp-govern mcp-govern` al terminal per veure l'error concret. |

## Deteccio de corrupcio

El servidor inclou instruccions que ensenyen a Claude a creuar dades i detectar patrons sospitosos automaticament. Quan l'usuari demana investigar, Claude aplica proactivament les seguents estrategies:

### 1. Fraccionament de contractes

Detectar si una entitat rep molts contractes menors (< 15.000EUR serveis, < 40.000EUR obres) del mateix departament. Indica possible fraccionament per evitar licitacio publica.

```
> L'empresa X fracciona contractes?
→ detectar_fraccionament(empresa="X")
```

Genera alertes automatiques:
- Acumulacio significativa de contractes menors
- Import mitja elevat (prop del limit legal)
- Tots els contractes del mateix departament

### 2. Concentracio de proveidors

Identificar empreses que acumulen un percentatge anomal del volum de contractacio d'un departament o organisme.

```
> Quines empreses acaparen els contractes del Departament de Salut?
→ detectar_concentracio_contractes(departament="Salut", any="2024")
```

### 3. Lobby → Contracte

Correlacionar reunions amb grups d'interes i contractes o subvencions adjudicats poc despres al mateix sector o entitat.

```
> Quins lobbies s'han reunit amb el conseller d'Economia? Han rebut contractes despres?
→ cercar_agenda_lobbies(departament="Economia") + cercar_contractes(adjudicatari="...")
```

### 4. Porta giratoria (revolving door)

Creuar alts carrecs cessats amb empreses que reben contractes o subvencions poc despres del cessament.

```
> Quins alts carrecs han cessat recentment? Les seves empreses reben contractes publics?
→ cercar_declaracions_activitats(actiu=false) + cercar_contractes(adjudicatari="...")
```

### 5. Retribucions anomales

Directius d'entitats subvencionades que cobren per sobre dels alts carrecs de la Generalitat (el president cobra 146.635EUR).

```
> Quins directius d'entitats subvencionades cobren mes que el president?
→ cercar_retribucions_subvencionats() vs cercar_retribucions_alts_carrecs(carrec="president")
```

### 6. Subvencions opaques

Beneficiaris que apareixen com "Benef. no publicable" a RAISC (Socrata) pero que si es poden identificar a la BDNS. Creuar codi BDNS entre ambdues fonts.

```
> Qui son els "Benef. no publicable" de les subvencions d'educacio?
→ cercar_subvencions(departament="Educacio") → obtenir codi_bdns → bdns_cercar_concessions()
```

### 7. Viatges sospitosos

Viatges a l'estranger amb despeses desproporcionades, sense motiu clar, o a destinacions no relacionades amb la funcio.

```
> Quins viatges han costat mes de 5.000EUR? Estaven justificats?
→ cercar_viatges_alts_carrecs()
```

### 8. Nepotisme en llocs de treball

Llocs de treball eventual o de lliure designacio concentrats en un departament.

```
> Quants llocs de lliure designacio te el Departament de Presidencia?
→ cercar_llocs_treball(departament="Presidencia")
```

### Principis d'analisi

Quan presenta resultats d'investigacio, Claude:

- Es basa **nomes en dades verificables** retornades per les tools
- Distingeix clarament entre **FETS** (dades) i **INDICIS** (patrons sospitosos)
- **No acusa directament** — presenta els patrons i deixa que l'usuari tregui conclusions
- Suggereix sempre **linies d'investigacio addicionals** per aprofundir

## Tools disponibles (34)

### Investigacio

| Tool | Descripcio |
|---|---|
| `investigar_entitat` | **Investiga una empresa o persona creuant TOTES les fonts** (contractes, menors, PSCP, subvencions, lobbies, retribucions, declaracions, viatges) en una sola crida. Genera un informe complet. |
| `detectar_concentracio_contractes` | Detecta empreses que acumulen un % anomal de contractes d'un departament. Top N per nombre i import. |
| `detectar_fraccionament` | Analitza si una empresa rep molts contractes menors sospitosos. Calcula imports, distribucio per departament i genera alertes automatiques. |

### Contractacio publica

| Tool | Descripcio |
|---|---|
| `cercar_contractes` | Registre public de contractes. Filtra per any, tipus, adjudicatari, organisme, import. |
| `cercar_publicacions_pscp` | Plataforma de Serveis de Contractacio Publica. Licitacions, adjudicacions, formalitzacions. |
| `cercar_contractes_menors` | Contractes menors (adjudicacio directa). Filtra per any, empresa, departament. |
| `detall_contracte` | Detall complet d'un contracte per codi d'expedient. |

### Subvencions (Catalunya - RAISC)

| Tool | Descripcio |
|---|---|
| `cercar_subvencions` | Subvencions concedides al RAISC. Filtra per any, beneficiari, departament, import. Les persones fisiques apareixen com "Benef. no publicable". |
| `cercar_convocatories` | Convocatories de subvencions. Filtra per any, departament, finalitat. |
| `detall_subvencio` | Detall d'una subvencio per codi RAISC o BDNS. |

### Subvencions (Espanya - BDNS)

| Tool | Descripcio |
|---|---|
| `bdns_cercar_concessions` | Subvencions de tota Espanya. **Inclou noms reals** de beneficiaris (persones fisiques i juridiques). Filtra per dates. |
| `bdns_cercar_convocatories` | Convocatories de subvencions a nivell estatal. |
| `bdns_detall_convocatoria` | Detall complet d'una convocatoria BDNS. |

### Retribucions i sous

| Tool | Descripcio |
|---|---|
| `cercar_retribucions_alts_carrecs` | **Sous nominals** d'alts carrecs: nom, cognom, carrec, departament i retribucio anual. Filtra per nom o per carrec (president, conseller, etc.). |
| `cercar_directius_sector_public` | **Sous nominals** de directius d'entitats publiques (ICF, TVC, hospitals, etc.). |
| `cercar_retribucions_subvencionats` | Retribucions de directius d'entitats que reben subvencions >10.000EUR. |
| `consultar_taules_salarials` | Taules salarials per cos: `alts_carrecs`, `funcionaris`, `laborals`, `mossos`, `bombers`, `agents_rurals`, `penitenciaris`. |

### Pressupostos

| Tool | Descripcio |
|---|---|
| `cercar_pressupostos` | Pressupostos aprovats de la Generalitat. Filtra per exercici, departament, programa. |
| `cercar_pressupostos_municipals` | Pressupostos dels ens municipals de Catalunya. |

### Personal i llocs de treball

| Tool | Descripcio |
|---|---|
| `cercar_llocs_treball` | Relacio de Llocs de Treball (RLT). Funcionaris i laborals. Filtra per departament, lloc, localitat. |
| `cercar_oferta_ocupacio` | Oferta d'ocupacio publica: places, cos, escala, grup. |

### Transparencia - Alts carrecs

| Tool | Descripcio |
|---|---|
| `cercar_declaracions_activitats` | Declaracions d'activitats publiques i privades. Participacions, consells, patrimoni. |
| `cercar_agenda_lobbies` | Reunions d'alts carrecs amb grups d'interes (lobbies). Qui es reuneix amb qui, sobre que. |
| `cercar_viatges_alts_carrecs` | Viatges a l'estranger. Destinacio, motiu, despeses desglossades. |

### datos.gob.es (Espanya)

| Tool | Descripcio |
|---|---|
| `datosgob_cercar_datasets` | Cerca datasets al cataleg nacional de dades obertes (113.000+ datasets). Filtra per tematica, organisme publicador i format. |
| `datosgob_detall_dataset` | Detall complet d'un dataset de datos.gob.es amb distribucions i metadades. |

### CGPJ - Poder Judicial (Espanya)

| Tool | Descripcio |
|---|---|
| `cgpj_dades_corrupcio` | Repositori de processos per corrupcio del CGPJ: macrocauses, Audiencia Nacional i tribunals superiors. |
| `cgpj_cercar_sentencies` | Cercador de sentencies al CENDOJ. Filtra per text, organ judicial, tipus de resolucio i dates. |
| `cgpj_estadistiques_judicials` | Estadistiques judicials per tema (penal, civil, contenciós), territori i any. |

### Open Data Barcelona

| Tool | Descripcio |
|---|---|
| `bcn_cercar_datasets` | Cerca entre 553 datasets municipals de Barcelona: pressupostos, contractes, seguretat, transport, medi ambient, habitatge. |
| `bcn_detall_dataset` | Detall d'un dataset de Barcelona amb la llista de recursos i els seus resource_id. |
| `bcn_obtenir_dades` | Obte dades d'un recurs concret de Barcelona via l'API datastore. |

### Utilitats

| Tool | Descripcio |
|---|---|
| `llistar_camps` | Mostra els camps disponibles de qualsevol dataset. Util abans d'usar `estadistiques`. |
| `estadistiques` | Agregacions (count/sum) sobre qualsevol dataset agrupades per qualsevol camp. |

## Exemples d'us

### Investigar una empresa

> Investiga Telefonica: contractes, subvencions, reunions amb lobbies, tot.

Usa `investigar_entitat` amb `nom="Telefonica"`. Creua 10 fonts de dades en paral·lel i genera un informe amb totes les aparicions.

### Detectar fraccionament de contractes

> L'empresa X rep molts contractes menors del Departament de Salut?

Usa `detectar_fraccionament` amb `empresa="X"`. Genera alertes automatiques si detecta patrons sospitosos (acumulacio d'imports, concentracio en un departament, imports prop del limit legal).

### Qui acapara els contractes?

> Quines empreses concentren mes contractes del Departament d'Educacio el 2024?

Usa `detectar_concentracio_contractes` amb `departament="Educacio"`, `any="2024"`.

### Lobby → Contracte

> Quins lobbies s'han reunit amb el Departament de Salut? Han rebut contractes despres?

Claude creua `cercar_agenda_lobbies` + `cercar_contractes` automaticament gracies a les instruccions del servidor.

### Porta giratoria

> Quins alts carrecs han cessat recentment? Les seves empreses reben contractes?

Claude creua `cercar_declaracions_activitats` (inactius) + `cercar_contractes`.

### Qui cobra mes a la Generalitat?

> Quant cobra el president de la Generalitat?

Usa `cercar_retribucions_alts_carrecs` amb `carrec="president de la generalitat"`.

### Sous dels Mossos d'Esquadra

> Quant cobra un inspector dels Mossos el 2024?

Usa `consultar_taules_salarials` amb `cos="mossos"`, `categoria="Inspector"`.

### Subvencions amb noms reals

> Qui ha rebut subvencions publiques al marc 2026?

Usa `bdns_cercar_concessions` amb `data_desde="01/03/2026"`, `data_fins="31/03/2026"`. La BDNS inclou noms de persones fisiques (amb NIF parcialment ocult).

### Reunions amb lobbies

> Amb quins grups d'interes s'ha reunit el Departament d'Economia?

Usa `cercar_agenda_lobbies` amb `departament="Economia"`.

### Viatges a l'estranger

> Quins viatges han fet els alts carrecs el 2025? Quant han costat?

Usa `cercar_viatges_alts_carrecs`. Retorna destinacio, motiu, despeses desglossades (dietes, allotjament, transport).

### Pressupost d'un municipi

> Quin es el pressupost de Girona pel 2024?

Usa `cercar_pressupostos_municipals` amb `municipi="Girona"`, `any_exercici="2024"`.

### Sentencies de corrupcio

> Busca sentencies sobre malversacio a l'Audiencia Nacional dels ultims 2 anys.

Usa `cgpj_cercar_sentencies` amb `text="malversación"`, `organ="AN"`.

### Processos per corrupcio

> Quines macrocauses de corrupcio te registrades el CGPJ?

Usa `cgpj_dades_corrupcio` per obtenir el repositori de processos per corrupcio.

### Dades obertes de Barcelona

> Quin es el pressupost de despeses de l'Ajuntament de Barcelona?

Usa `bcn_detall_dataset` amb `dataset_name="pressupost-despeses"` per obtenir els recursos, despres `bcn_obtenir_dades` per consultar les dades.

### Datasets nacionals

> Quins datasets de contractacio publica hi ha a datos.gob.es?

Usa `datosgob_cercar_datasets` amb `query="contratos públicos"`.

## Datasets

### Contractacio

| Clau | ID | Font |
|---|---|---|
| `contractes` | `hb6v-jcbf` | Registre public de contractes |
| `pscp` | `ybgg-dgi6` | Publicacions PSCP |
| `contractes_menors` | `qjue-2pk9` | Contractacio menor |
| `adjudicacions` | `nn7v-4yxe` | Adjudicacions Generalitat |

### Subvencions

| Clau | ID | Font |
|---|---|---|
| `subvencions` | `s9xt-n979` | Concessions RAISC |
| `convocatories` | `khxn-nv6a` | Convocatories RAISC |

### Retribucions

| Clau | ID | Font |
|---|---|---|
| `retrib_alts_carrecs` | `x9au-abcn` | Alts carrecs (nominal) |
| `retrib_directius_sector_public` | `62n8-i8x7` | Directius sector public |
| `retrib_directius_subvencionats` | `ut3h-wvbc` | Directius entitats subvencionades |
| `taules_retrib_alts_carrecs` | `3b6m-hrxk` | Taules retributives alts carrecs |
| `retrib_funcionaris` | `b4zx-cfga` | Personal funcionari |
| `retrib_laborals` | `abap-7r6z` | Personal laboral |
| `retrib_mossos` | `8avk-cyhk` | Mossos d'Esquadra |
| `retrib_bombers` | `i5pb-qsvh` | Bombers |
| `retrib_agents_rurals` | `xvaz-qxjx` | Agents rurals |
| `retrib_penitenciaris` | `he84-trmn` | Centres penitenciaris |

### Pressupostos

| Clau | ID | Font |
|---|---|---|
| `pressupostos` | `yd9k-7jhw` | Pressupostos Generalitat |
| `execucio_pressupost` | `ajns-4mi7` | Execucio mensual despeses |
| `pressupostos_municipals` | `4g9s-gzp6` | Pressupostos municipals |

### Personal

| Clau | ID | Font |
|---|---|---|
| `rlt_funcionaris` | `cywt-i78c` | RLT funcionaris |
| `rlt_laborals` | `g25x-kht6` | RLT laborals |
| `oferta_ocupacio` | `52mi-tgq5` | Oferta d'ocupacio publica |

### Transparencia

| Clau | ID | Font |
|---|---|---|
| `declaracions_activitats` | `vdss-2ppz` | Activitats alts carrecs |
| `agenda_lobbies` | `hd8k-y28e` | Reunions amb lobbies |
| `viatges_alts_carrecs` | `5kte-hque` | Viatges a l'estranger |
| `docencia_alts_carrecs` | `w7dd-bwpy` | Docencia universitaria |

### Fiscalitat

| Clau | ID | Font |
|---|---|---|
| `impost_successions_composicio` | `2jqq-fyu8` | Impost sobre successions per composicio de l'herencia |
| `impost_successions_quota` | `xaxt-fghh` | Impost sobre successions - calcul de la quota final |

### Carrecs locals

| Clau | ID | Font |
|---|---|---|
| `retrib_carrecs_locals` | `bepu-nr6b` | Indicadors retributius dels carrecs electes locals |

### Participacio

| Clau | ID | Font |
|---|---|---|
| `enquestes_opinio` | `gp4k-sxxn` | Microdades d'estudis d'opinio |
| `participacio_ciutadana` | `62wr-uxxx` | Panel de participacio ciutadana |

### Contractacio local

| Clau | ID | Font |
|---|---|---|
| `relic` | `t3wj-j4pu` | Registre public de contractes d'ens locals (RELIC) |

### Serveis socials

| Clau | ID | Font |
|---|---|---|
| `serveis_residencials_violencia` | `vqd5-kgke` | Serveis residencials per a dones en situacio de violencia |

### Educacio

| Clau | ID | Font |
|---|---|---|
| `centres_fp` | `iyus-443e` | Centres de formacio professional integrada |

### Infraestructures i medi ambient

| Clau | ID | Font |
|---|---|---|
| `ports` | `frcw-v3xi` | Ports de Catalunya |
| `depuradores` | `k288-dig3` | Sistemes de sanejament i depuradores |
| `economia_circular` | `5jbn-usiv` | Iniciatives Catalunya Circular |

### Agricultura

| Clau | ID | Font |
|---|---|---|
| `explotacions_agraries` | `uwe8-jqcu` | Parcel·les i cultius de les explotacions agraries (DUN) |

### BDNS (API REST)

| Endpoint | Descripcio |
|---|---|
| `/api/concesiones/busqueda` | Concessions de tota Espanya (amb noms reals) |
| `/api/convocatorias/busqueda` | Convocatories estatals |
| `/api/convocatorias?numConv=X` | Detall convocatoria |

### datos.gob.es (API REST)

| Endpoint | Descripcio |
|---|---|
| `/apidata/catalog/dataset.json` | Cataleg de 113.000+ datasets nacionals |
| `/apidata/catalog/distribution.json` | Distribucions (fitxers i APIs) dels datasets |

### CGPJ (API REST / PC-Axis)

| Endpoint | Descripcio |
|---|---|
| `/stj/pcaxis/juzgados.json` | Estadistiques judicials |
| `/stj/pcaxis/corrupcion.json` | Processos per corrupcio |
| `/search/indexAN` | Cercador de sentencies CENDOJ |

### Open Data BCN (API CKAN)

| Endpoint | Descripcio |
|---|---|
| `/data/api/action/package_search` | Cerca de datasets municipals |
| `/data/api/action/package_show` | Detall d'un dataset |
| `/data/api/action/datastore_search` | Consulta de dades d'un recurs |

Datasets destacats de Barcelona:

| Clau | Dataset | Area |
|---|---|---|
| `pressupost_despeses` | `pressupost-despeses` | Pressupostos |
| `pressupost_ingressos` | `pressupost-ingressos` | Pressupostos |
| `contractes_menors` | `contractes-menors` | Contractacio |
| `relacio_contractistes` | `relacio-contractistes` | Contractacio |
| `incidents_gub` | `incidents-gestionats-gub` | Seguretat |
| `qualitat_aire` | `qualitat-aire-detall-bcn` | Medi ambient |
| `habitatges_turistic` | `habitatges-us-turistic` | Habitatge |
| `renda_llars` | `renda-disponible-llars-bcn` | Economia |
| `bicing` | `bicing` | Transport |
| `obres` | `obres` | Urbanisme |

## Llicencia

MIT

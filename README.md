# mcp-govern

Servidor MCP (Model Context Protocol) expert en **transparencia publica** i **deteccio de patrons de corrupcio** a partir de dades obertes del **Govern de Catalunya** i la **BDNS** d'Espanya.

Contractes, subvencions, sous, pressupostos, lobbies, viatges — 26 tools que creuen automaticament 30+ datasets per trobar anomalies, fraccionaments i conflictes d'interes.

## Que es un MCP?

Un MCP (Model Context Protocol) es un servidor que dona "superpoderes" a Claude (o altres LLMs). En aquest cas, permet que Claude consulti en temps real les bases de dades publiques del Govern de Catalunya i d'Espanya. Tu preguntes en llenguatge natural i Claude fa les consultes per tu.

Per exemple:
- *"Investiga Telefonica: contractes, subvencions, reunions amb lobbies"* → Claude creua 10 bases de dades en paral·lel
- *"Quant cobra el president de la Generalitat?"* → Claude consulta les taules retributives oficials
- *"Quines empreses acaparen els contractes menors de Salut?"* → Claude detecta concentracio sospitosa

**No necessites saber programar.** Nomes cal instal·lar-lo i preguntar.

## Fonts de dades

| Font | Abast | API |
|---|---|---|
| [analisi.transparenciacatalunya.cat](https://analisi.transparenciacatalunya.cat) | Catalunya | Socrata (SODA) |
| [BDNS](https://www.pap.hacienda.gob.es/bdnstrans/) | Espanya | REST |

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

## Tools disponibles (26)

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

### BDNS (API REST)

| Endpoint | Descripcio |
|---|---|
| `/api/concesiones/busqueda` | Concessions de tota Espanya (amb noms reals) |
| `/api/convocatorias/busqueda` | Convocatories estatals |
| `/api/convocatorias?numConv=X` | Detall convocatoria |

## Llicencia

MIT

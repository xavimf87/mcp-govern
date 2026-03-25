# Changelog

Totes les modificacions destacables d'aquest projecte queden documentades aqui.

El format segueix [Keep a Changelog](https://keepachangelog.com/ca/1.1.0/) i el projecte usa [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **CI/CD**: Pipeline de GitHub Actions amb 5 jobs (lint, typecheck, test, integration, build)
- **Tool `dogc_cercar_normativa`**: Cerca normativa al DOGC (lleis, decrets, ordres, resolucions) via Socrata
- **Tool `pge_despeses`**: Descarrega i parseja CSV amb imports reals per programa/ministeri dels PGE
- **BDNS cerca per text**: Nous parametres `texto`, `organo` i `comunitat` a `bdns_cercar_concessions`
- **BOE legislacio amb filtres**: Nous parametres `titol`, `departament`, `rang` i `materia` a `boe_legislacio`
- **CIF/NIF a `investigar_entitat`**: Parametre opcional `cif` per identificacio univoca (cerca PSCP + subvencions per CIF)
- **Normalitzacio de tipus de contracte**: Les estadistiques fusionen duplicats ("SERVEIS" → "5. SERVEIS")
- **Post-filtre de rellevancia**: `investigar_entitat` filtra resultats que no contenen el terme cercat
- **Linting i type checking**: Configuracio de ruff i mypy al `pyproject.toml`
- **Tests d'integracio**: Smoke tests contra APIs reals (1 crida per font)
- 27 nous tests unitaris (168 total)

### Fixed
- **Bug `_normalize_accents`**: Reemplacava TOTES les vocals amb `%`, fent que "Accenture" es convertis en "%cc%nt%r%" i retornes resultats no relacionats. Ara nomes reemplaca vocals accentuades (`a`, `e`, `i` → sense canvi; `a`, `e`, `i` → `%`)
- **Bug `investigar_entitat`**: Retornava resultats no relacionats (ex: cercar "Accenture" retornava "ACCESIBILITAT GLOBAL"). Ara post-filtra per verificar que el terme apareix als resultats

### Changed
- `bdns_cercar_concessions`: Accepta text lliure, organ i comunitat autonoma a mes de dates
- `boe_legislacio`: Accepta titol, departament, rang normatiu i materia a mes de paginacio
- `investigar_entitat`: Accepta parametre `cif` opcional per cerca per CIF/NIF
- Instruccions del servidor (`_INSTRUCTIONS`) actualitzades amb les noves tools i fonts

## [0.1.0] - 2025-05-01

### Added
- **10 fonts de dades**: Socrata, BDNS, datos.gob.es, CGPJ, Open Data BCN, BOE, BORME, INE, Banc d'Espanya, PGE
- **47 tools MCP** per consultar dades obertes
- **3 tools d'investigacio**: `investigar_entitat`, `detectar_concentracio_contractes`, `detectar_fraccionament`
- **Contractacio publica**: `cercar_contractes`, `cercar_publicacions_pscp`, `cercar_contractes_menors`, `detall_contracte`
- **Subvencions Catalunya (RAISC)**: `cercar_subvencions`, `cercar_convocatories`, `detall_subvencio`
- **Subvencions Espanya (BDNS)**: `bdns_cercar_concessions`, `bdns_cercar_convocatories`, `bdns_detall_convocatoria`
- **Retribucions**: `cercar_retribucions_alts_carrecs`, `cercar_directius_sector_public`, `cercar_retribucions_subvencionats`, `consultar_taules_salarials`
- **Pressupostos**: `cercar_pressupostos`, `cercar_pressupostos_municipals`
- **Personal**: `cercar_llocs_treball`, `cercar_oferta_ocupacio`
- **Transparencia**: `cercar_declaracions_activitats`, `cercar_agenda_lobbies`, `cercar_viatges_alts_carrecs`
- **datos.gob.es**: `datosgob_cercar_datasets`, `datosgob_detall_dataset`
- **CGPJ**: `cgpj_dades_corrupcio`, `cgpj_cercar_sentencies`, `cgpj_estadistiques_judicials`
- **Barcelona**: `bcn_cercar_datasets`, `bcn_detall_dataset`, `bcn_obtenir_dades`
- **BOE**: `boe_sumari`, `boe_nomenaments`, `boe_contractes`, `boe_legislacio`, `boe_departaments`
- **BORME**: `borme_sumari`
- **INE**: `ine_operacions`, `ine_taules`, `ine_dades_taula`, `ine_serie`
- **Banc d'Espanya**: `bde_serie`, `bde_series_destacades`
- **PGE**: `pge_estructura`
- **Utilitats**: `llistar_camps`, `estadistiques`
- Deteccio automatica de 8 patrons de corrupcio (fraccionament, porta giratoria, lobby→contracte, concentracio, retribucions anomales, subvencions opaques, viatges sospitosos, nepotisme)
- Normalitzacio d'accents catalans a les cerques
- Conversio automatica d'imports de centims a euros (contractes menors)
- 141 tests unitaris amb pytest + respx

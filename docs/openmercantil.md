# Proposta documental: OpenMercantil com a capa opcional de context mercantil

Aquesta proposta descriu una integracio minima, opcional i no invasiva entre `mcp-govern` i OpenMercantil.

L'objectiu no es substituir cap font oficial de `mcp-govern`, sino afegir una capa complementaria de context mercantil espanyol quan una investigacio ja ha detectat una empresa, adjudicatari, beneficiari, proveidor o entitat relacionada amb contractacio publica, subvencions o altres fonts obertes.

OpenMercantil es una eina independent de reutilitzacio i consulta d'informacio publica mercantil. No es el BOE, el BORME, el Registre Mercantil, una administracio publica ni un servei de certificacio. Tampoc hauria d'utilitzar-se per fer acusacions, scoring creditici o conclusions juridiques. Per a validesa oficial cal consultar sempre les fonts originals.

## Encaix dins de mcp-govern

L'encaix mes prudent seria exposar OpenMercantil com a bloc separat dins de respostes d'investigacio, amb una capcalera clara:

```text
Context mercantil complementari (OpenMercantil, font independent no oficial)
```

Pot aportar valor especialment a:

- `investigar_entitat`
- fluxos de contractacio publica
- fluxos de subvencions
- comprovacions preliminars de proveidors o beneficiaris
- desambiguacio de noms socials quan hi ha coincidencies multiples
- context BORME estructurat abans d'anar a la font oficial

## Flux minim proposat

1. `mcp-govern` detecta una empresa o entitat en una consulta.
2. Si hi ha CIF/NIF, es consulta OpenMercantil amb aquest identificador o amb el nom social.
3. Es recuperen candidats amb `slug`, nom, CIF, nombre d'actes i ultima aparicio.
4. Si hi ha una coincidencia prou clara, es consulta la fitxa d'empresa.
5. La resposta final mostra el resultat com a context complementari, separat de les fonts oficials.
6. Si hi ha ambiguitat, es mostren candidats i no es forca una conclusio.

## Endpoints reals verificats

Documentacio:

- https://openmercantil.es/api/documentacion
- https://openmercantil.es/openapi.json

Endpoints inicials recomanats:

```http
GET https://openmercantil.es/api/v1/search?q={consulta}&limit=5
GET https://openmercantil.es/api/v1/company/{slug}
GET https://openmercantil.es/api/v1/company/{slug}/events
GET https://openmercantil.es/api/v1/company/{slug}/officers
GET https://openmercantil.es/api/v1/company/{slug}/contracts
GET https://openmercantil.es/api/v1/company/{slug}/grants
GET https://openmercantil.es/api/v1/company/{slug}/sources
```

Per una primera versio documental o experimental, bastaria amb:

```text
openmercantil_search(query, limit=5)
openmercantil_company(slug)
```

## Exemple 1: cerca i desambiguacio

Consulta:

```http
GET https://openmercantil.es/api/v1/search?q=mercadona&limit=2
```

Resposta observada:

```json
{
  "query": "mercadona",
  "count": 2,
  "items": [
    {
      "slug": "mercadona-sa",
      "name": "MERCADONA SA",
      "cif": "A46103834",
      "acts_count": 260,
      "last_seen": "2026-06-29",
      "aliases": ["mercadona", "mercadona sa"]
    }
  ],
  "_attributions": {
    "borme": "Fuente: BORME — Boletin Oficial del Registro Mercantil (Agencia Estatal BOE)."
  }
}
```

Us dins de `mcp-govern`:

- si el CIF esperat es `A46103834`, la coincidencia es forta;
- si nomes hi ha nom social, cal mostrar candidats si hi ha mes d'una coincidencia;
- no s'hauria de deduir identitat si el nom es ambigu.

## Exemple 2: fitxa d'empresa

Consulta:

```http
GET https://openmercantil.es/api/v1/company/mercadona-sa
```

Camps inicials utils per una resposta curta:

```json
{
  "company": {
    "name": "MERCADONA SA",
    "cif": "A46103834",
    "status": "Activa"
  },
  "kpis": {
    "acts_count": 260,
    "first_seen": "2009-01-23",
    "last_seen": "2026-06-29"
  },
  "_data_sources_used": [
    {
      "name": "Boletin Oficial del Registro Mercantil",
      "official_url": "https://www.boe.es/diario_borme/"
    }
  ]
}
```

Sortida recomanada dins de `mcp-govern`:

```text
Context mercantil complementari (OpenMercantil, font independent no oficial):
- Empresa: MERCADONA SA
- CIF: A46103834
- Estat detectat: Activa
- Actes registrals agregats: 260
- Primera aparicio detectada: 2009-01-23
- Darrera aparicio detectada: 2026-06-29
- Font reutilitzada: BORME / Agencia Estatal BOE

Nota: informacio de context. No substitueix certificats oficials ni verificacio registral.
```

## Exemple 3: actes i carrecs

Per ampliar el context quan l'usuari ho demani explicitament:

```http
GET https://openmercantil.es/api/v1/company/mercadona-sa/events
GET https://openmercantil.es/api/v1/company/mercadona-sa/officers
```

Us suggerit:

- mostrar nomes actes recents o rellevants;
- evitar llistats massa llargs per defecte;
- conservar sempre data, tipus d'acte, font i enllac quan estigui disponible;
- separar persones/carrecs de conclusions sobre responsabilitat o conflicte d'interes.

## Exemple 4: contractacio i subvencions

Si `mcp-govern` ja esta investigant contractes o subvencions, OpenMercantil podria aportar un resum complementari:

```http
GET https://openmercantil.es/api/v1/company/mercadona-sa/contracts
GET https://openmercantil.es/api/v1/company/mercadona-sa/grants
```

Aquest bloc hauria de quedar sempre subordinat a les fonts oficials que `mcp-govern` ja consulta. OpenMercantil pot ajudar a agregar o contextualitzar, pero la verificacio principal ha de continuar en els datasets oficials corresponents.

## Esquema de sortida suggerit

```json
{
  "source": "openmercantil",
  "source_label": "OpenMercantil, independent non-official public-data reuse layer",
  "query": "mercadona",
  "matched_company": {
    "name": "MERCADONA SA",
    "cif": "A46103834",
    "slug": "mercadona-sa",
    "url": "https://openmercantil.es/empresa/mercadona-sa"
  },
  "summary": {
    "status": "Activa",
    "acts_count": 260,
    "first_seen": "2009-01-23",
    "last_seen": "2026-06-29"
  },
  "warnings": [
    "Independent and non-official reuse layer",
    "Does not replace BOE/BORME/Registro Mercantil certificates",
    "Use as context, not as legal or credit-scoring conclusion"
  ]
}
```

## Criteris de seguretat i qualitat

- No activar per defecte si l'usuari demana nomes dades oficials.
- Mostrar OpenMercantil com a font complementaria i independent.
- No barrejar OpenMercantil amb les fonts oficials en el mateix bloc de proves.
- No fer acusacions ni inferencies sobre persones o empreses a partir d'un acte BORME aillat.
- Si hi ha diversos candidats, mostrar-los o demanar desambiguacio.
- Si OpenMercantil no respon, la resta de `mcp-govern` ha de continuar funcionant.
- Evitar cachejar dades personals sensibles mes enlla dels resultats necessaris per la resposta.
- Enllacar sempre la font oficial quan sigui possible.

## Valor per a usuaris

Aquesta integracio pot ajudar a entendre millor el context mercantil d'empreses espanyoles que apareixen en contractes, subvencions, lobbies o investigacions de transparencia, sense convertir OpenMercantil en una font oficial ni en un sistema de scoring.

També pot ajudar a detectar quan cal aprofundir en fonts oficials: BORME, BOE, Registre Mercantil, expedients de contractacio o datasets de subvencions.
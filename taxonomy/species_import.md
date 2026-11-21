# Artimport – filformat och beteende

Den gemensamma importmotorn finns i `taxonomy/species_import.py` och används både av management-kommandot och administrationsgränssnittet. Samma information finns som hjälpsida från artimporten i Django Admin.

Importfilen är JSON med formatversion 1:

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Aulonocara",
      "scientific_name": "stuartgranti",
      "breeding_class": "silver",
      "swedish_names": ["Påfågelciklid"],
      "english_names": ["Flavescent peacock"],
      "scientific_synonyms": [],
      "geographies": ["Afrika", "Malawi"],
      "links": [
        {
          "url": "https://example.org/aulonocara-stuartgranti",
          "source_name": "Example",
          "title": "Aulonocara stuartgranti"
        }
      ]
    }
  ]
}
```

## Fält per art

`genus` och `scientific_name` är alltid obligatoriska och identifierar arten. Matchningen mot befintligt genus, aktuellt vetenskapligt namn och vetenskapliga synonymer är skiftlägesokänslig. Importen ändrar däremot inte stavningen/casing på en befintlig post.

`breeding_class` är `bronze` (Brons, 1 poäng), `silver` (Silver, 3 poäng), `gold` (Guld, 7 poäng), `elite` (Elit, 7 poäng) eller `unrated` (Ej bedömd, preliminärt 1 poäng). Fältet krävs när en ny art skapas men kan utelämnas när en befintlig art bara kompletteras. Om fältet anges för en befintlig art uppdateras artens odlingsklass till det angivna värdet. När en art ändras från Ej bedömd till en faktisk klass uppdateras även tidigare godkända odlingar som fortfarande har Ej bedömd som tilldelad klass; individuellt bedömda odlingar behåller sin historiska klass.

`cl_number` är valfritt och används för L-, C- och CW-nummer, till exempel `L046`, `C123` eller `CW009`. Whitespace tas bort och värdet normaliseras till versaler, så exempelvis `l 046` sparas som `L046` och `cw 009` som `CW009`. För en befintlig art kompletteras fältet bara om arten ännu saknar C/L-nummer.

`swedish_names` är en lista med svenska populärnamn. Minst ett svenskt namn krävs när en ny art skapas. För en befintlig art är listan valfri. Det första namnet används som primärt svenskt namn om arten saknar ett; annars bevaras befintligt primärnamn och ett nytt första namn registreras som synonym när det skiljer sig.

`english_names` är valfri. Det första namnet används som primärt engelskt namn om det saknas; övriga alternativa namn lagras som synonymer.

`scientific_synonyms` är valfri och innehåller fullständiga tidigare vetenskapliga namn, till exempel `Lebistes reticulatus`.

`geographies` är en valfri lista med geografiska områden, till exempel `["Afrika", "Malawi"]`. En art kan ha flera geografier. Geografier återanvänds skiftlägesokänsligt, så `malawi` matchar en befintlig `Malawi`, samtidigt som den befintliga stavningen bevaras.

`links` är valfri. Varje länk kräver `url`. `source_name` och `title` är valfria. Om `source_name` saknas härleds det från domänen. Om `title` saknas försöker importen läsa HTML-sidans `<title>`; misslyckad hämtning stoppar inte importen.

## Full import av en ny art

För en art som ännu inte finns måste importposten minst innehålla:

```json
{
  "genus": "Hypancistrus",
  "scientific_name": "zebra",
  "breeding_class": "gold",
  "swedish_names": ["Zebramal"],
  "cl_number": "L 046"
}
```

`cl_number` och `geographies` är valfria även vid ny art. Saknas `breeding_class` eller `swedish_names` när en ny art behöver skapas avbryts den artposten med valideringsfel. Importen är atomisk per artpost, så en misslyckad post ska inte lämna kvar delvis skapad data.

## Kompletterande import av en befintlig art

När arten redan finns räcker `genus` + `scientific_name` tillsammans med de fält som ska kompletteras. Exempel som lägger till ett C/L-nummer, ytterligare geografi och en extern länk:

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Hypancistrus",
      "scientific_name": "zebra",
      "cl_number": "L 046",
      "geographies": ["Sydamerika"],
      "links": [
        {
          "url": "https://example.org/hypancistrus-zebra",
          "source_name": "Example"
        }
      ]
    }
  ]
}
```

Kompletteringsimporten är i huvudsak additiv. Fält som saknas i importfilen tar inte bort eller nollställer befintliga namn, synonymer, geografier, länkar, `breeding_class` eller `cl_number`. Ett uttryckligen angivet `breeding_class` uppdaterar däremot odlingsklassen även för en befintlig art. Ett angivet `cl_number` fyller ett tomt fält men ersätter inte ett redan registrerat nummer. Angivna geografier läggs till; andra befintliga geografier ligger kvar. Samma fil kan importeras flera gånger utan att skapa dubbletter.

## Import via gammalt vetenskapligt namn

Om `genus` + `scientific_name` inte matchar en arts aktuella namn försöker importen matcha den fullständiga kombinationen mot `SpeciesSynonym.scientific_name`.

Exempel: om `Lebistes reticulatus` finns som synonym till `Poecilia reticulata` kan en kompletteringsimport använda det gamla namnet utan att skapa en ny art.

Om samma gamla vetenskapliga namn finns som synonym för flera arter betraktas matchningen som tvetydig och importen ger ett valideringsfel i stället för att välja en art godtyckligt.

## Resultat och output

`import_species_file(path)` returnerar strukturerad statistik över skapade och återanvända genera, arter, synonymer, geografier, geografikopplingar och länkar. Själva importmotorn skriver inte till stdout eller stderr. Management-kommandot ansvarar själv för eventuell konsoloutput, och adminvyn presenterar samma returvärde i webbgränssnittet.


## Systematisk datakvalitetsgranskning

En kompletteringsrad för en **befintlig** art kan också ange `quality_review`. Det
registrerar en granskningsstatus även om ingen ytterligare uppgift har hittats.
Odlingsklass och befintliga artuppgifter påverkas inte när de utelämnas.

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Exempelgenus",
      "scientific_name": "exempelart",
      "quality_review": {
        "status": "reviewed",
        "reviewed_at": "2026-11-21",
        "fields": {
          "swedish_name": "not_found",
          "english_name": "found",
          "geography": "found",
          "links": "found"
        },
        "sources": ["https://example.org/species"],
        "notes": "Svenskt trivialnamn kunde inte beläggas."
      }
    }
  ]
}
```

Exemplet visar **format**, inte verifierade uppgifter eller källor. Använd
verkliga HTTPS-källor i riktiga filer. `status` är `reviewed` eller
`manual_review`. Varje fält måste ha ett av värdena `found`, `not_found`,
`uncertain` eller `not_checked`. `review_again_after` kan anges som
`YYYY-MM-DD`; för `reviewed` är standard 365 dagar efter `reviewed_at`,
medan `manual_review` saknar automatiskt omgranskningsdatum. Endast nyare
granskningsdatum uppdaterar en befintlig status; återimport av samma fil är
idempotent. Enbart existerande arter kan registreras på detta vis; använd rätt
C/L-nummer för tvetydiga identifieringar.

Skillen sparar en gemensam `data/species/data_quality_review_log.json` med
formatversion 1 på sin öppna PR-branch. Denna importfil innehåller en rad
per granskad art, även när inga kompletterande artuppgifter har hittats.
Efter godkänd PR/import blir granskningsstatus beständig i databasen.
Endpointen `/api/species/data-quality/random/` har kvar sin adress av
kompatibilitetsskäl men returnerar numera en prioriterad, sidindelad lista
med högst tio arter per sida, valbar via `?page=2`, och ett `next_page`-fält.
Granskade arter tas bort från urvalet tills omgranskning är aktuell.

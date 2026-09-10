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

`breeding_class` är `bronze`, `silver` eller `gold`. Fältet krävs när en ny art skapas men kan utelämnas när en befintlig art bara kompletteras.

`swedish_names` är en lista med svenska populärnamn. Minst ett svenskt namn krävs när en ny art skapas. För en befintlig art är listan valfri. Det första namnet används som primärt svenskt namn om arten saknar ett; annars bevaras befintligt primärnamn och ett nytt första namn registreras som synonym när det skiljer sig.

`english_names` är valfri. Det första namnet används som primärt engelskt namn om det saknas; övriga alternativa namn lagras som synonymer.

`scientific_synonyms` är valfri och innehåller fullständiga tidigare vetenskapliga namn, till exempel `Lebistes reticulatus`.

`geographies` är en valfri lista med geografiska områden, till exempel `["Afrika", "Malawi"]`. En art kan ha flera geografier. Geografier återanvänds skiftlägesokänsligt, så `malawi` matchar en befintlig `Malawi`, samtidigt som den befintliga stavningen bevaras.

`links` är valfri. Varje länk kräver `url`. `source_name` och `title` är valfria. Om `source_name` saknas härleds det från domänen. Om `title` saknas försöker importen läsa HTML-sidans `<title>`; misslyckad hämtning stoppar inte importen.

## Full import av en ny art

För en art som ännu inte finns måste importposten minst innehålla:

```json
{
  "genus": "Aulonocara",
  "scientific_name": "stuartgranti",
  "breeding_class": "silver",
  "swedish_names": ["Påfågelciklid"],
  "geographies": ["Afrika", "Malawi"]
}
```

`geographies` är valfritt även vid ny art. Saknas `breeding_class` eller `swedish_names` när en ny art behöver skapas avbryts den artposten med valideringsfel. Importen är atomisk per artpost, så en misslyckad post ska inte lämna kvar delvis skapad data.

## Kompletterande import av en befintlig art

När arten redan finns räcker `genus` + `scientific_name` tillsammans med de fält som ska kompletteras. Exempel som lägger till ytterligare geografi och en extern länk:

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Aulonocara",
      "scientific_name": "stuartgranti",
      "geographies": ["Malawi"],
      "links": [
        {
          "url": "https://example.org/malawi-reference",
          "source_name": "Example"
        }
      ]
    }
  ]
}
```

Kompletteringsimporten är additiv. Fält som saknas i importfilen tar inte bort eller nollställer befintliga namn, synonymer, geografier, länkar eller `breeding_class`. Angivna geografier läggs till; andra befintliga geografier ligger kvar. Samma fil kan importeras flera gånger utan att skapa dubbletter.

## Import via gammalt vetenskapligt namn

Om `genus` + `scientific_name` inte matchar en arts aktuella namn försöker importen matcha den fullständiga kombinationen mot `SpeciesSynonym.scientific_name`.

Exempel: om `Lebistes reticulatus` finns som synonym till `Poecilia reticulata` kan en kompletteringsimport använda det gamla namnet utan att skapa en ny art.

Om samma gamla vetenskapliga namn finns som synonym för flera arter betraktas matchningen som tvetydig och importen ger ett valideringsfel i stället för att välja en art godtyckligt.

## Resultat och output

`import_species_file(path)` returnerar strukturerad statistik över skapade och återanvända genera, arter, synonymer, geografier, geografikopplingar och länkar. Själva importmotorn skriver inte till stdout eller stderr. Management-kommandot ansvarar själv för eventuell konsoloutput, och adminvyn presenterar samma returvärde i webbgränssnittet.

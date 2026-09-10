# Externa länkar i artimporten

Varje art i BA-026-formatet kan ha en valfri `links`-lista:

```json
{
  "genus": "Mikrogeophagus",
  "scientific_name": "ramirezi",
  "breeding_class": "silver",
  "swedish_names": ["Fjärilsciklid"],
  "english_names": ["Ram cichlid"],
  "scientific_synonyms": ["Papiliochromis ramirezi"],
  "links": [
    {
      "url": "https://www.fishbase.se/summary/Mikrogeophagus-ramirezi.html",
      "source_name": "FishBase"
    },
    {
      "url": "https://www.ciklid.org/artregister/art.php?ID=442",
      "source_name": "NCS Artregister",
      "title": "Mikrogeophagus ramirezi - Nordiska Ciklidsällskapet artregister"
    }
  ]
}
```

`url` är obligatorisk. `source_name` och `title` är valfria vid import.

Om `source_name` saknas härleds det från domänen. FishBase, PlanetCatfish och NCS Artregister har särskilda läsbara namn. För andra domäner används domännamnet.

Om `title` saknas försöker importen läsa HTML-sidans `<title>`. Om sidan inte kan hämtas importeras länken ändå med tom titel. En uttryckligen angiven titel innebär att ingen titelhämtning behövs.

Länkar identifieras per art och URL. Samma importfil kan därför köras flera gånger utan att duplicera länkar, och samma externa URL får vid behov förekomma på flera olika arter.

## Komplettera en befintlig art

För en art som redan finns räcker `genus` och `scientific_name` för att identifiera posten. Därefter behöver importfilen bara innehålla den information som ska läggas till. Utelämnade fält tar inte bort eller nollställer befintlig information.

Exempel på en import som endast lägger till en ny extern länk:

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Poecilia",
      "scientific_name": "reticulata",
      "links": [
        {
          "url": "https://example.org/poecilia-reticulata",
          "source_name": "Example"
        }
      ]
    }
  ]
}
```

Om `genus` + `scientific_name` inte motsvarar en befintlig art måste posten fortfarande innehålla `breeding_class` och minst ett värde i `swedish_names`, eftersom de behövs för att skapa en ny art. En ofullständig post för en ny art ger valideringsfel och ska inte lämna kvar någon delvis skapad genus- eller artpost.

Om `genus` + `scientific_name` i stället motsvarar ett gammalt vetenskapligt namn som finns registrerat som synonym används den befintliga arten och kompletterande data läggs på den. Om samma vetenskapliga synonym finns på flera arter avbryts den posten med ett tydligt fel i stället för att välja en art godtyckligt.

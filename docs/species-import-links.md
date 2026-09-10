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

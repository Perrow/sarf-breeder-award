---
name: species-import
description: "Omvandla artlistor från valfritt källformat (tabeller, Markdown, CSV, Excel, JSON, fritext) till Odlingskampanjens versionsstyrda JSON-importfiler för arter. Använd vid nya artimporter, kompletteringar, synonymhantering, C/L/CW-nummer och valörer. Håll högst 100 artposter per fil och arbeta via PR."
---

# Artimport för Odlingskampanjen

## Syfte och källor

Skapa **importdata**, inte ändringar i applikationskoden. Inputens format kan variera, men output ska alltid följa `taxonomy/species_import.md` och `taxonomy/species_import.py` i **aktuell** branch av `Perrow/sarf-breeder-award`. Läs dessa innan arbetet; om specifikationen ändrats gäller aktuell kod och dokumentation före exemplen här.

Importfilerna hör hemma i `data/species/`. Skapa/uppdatera dem i en feature-/data-branch via GitHub och öppna eller uppdatera en PR. **Commita aldrig direkt till main.** Om användaren hänvisar till en befintlig import-PR, återanvänd den när den fortfarande är öppen. Om den är mergad, utgå från aktuell main och skapa ny branch/PR.

## Arbetsgång

1. **Läs materialet.** Ta emot tabeller, Markdown, CSV, Excel, JSON, ren text eller flera blandade källor. Identifiera rubriker och kolumner från faktiska data; anta inte att en viss kolumnposition eller enhet är densamma som förra gången. Om ett fält inte framgår, lämna det okänt.
2. **Läs importkontraktet.** Kontrollera `taxonomy/species_import.md`, importören, tillåtna `Species.BreedingClass`-värden och befintliga filer i `data/species/`.
3. **Tolkas utan att hitta på.** Extrahera vetenskapligt namn, vanliga namn, valör, geografi, C/L/CW-nummer, tidigare namn, lokalformer och verifierbara länkar. Bevara källans betydelse och notera felaktiga eller tvetydiga rader. Vid osäker synonymi: behåll källnamnet och markera för granskning; slå inte ihop arter på gissning.
4. **Jämför mot tidigare importdata.** Matcha på normaliserad kombination av släkte, artnamn och `cl_number`, samt dokumenterade vetenskapliga synonymer. Det måste också gå att ha flera `Genus sp.`-poster med **olika** L/C/CW-nummer. Behandla aldrig två olika nummer som samma art utan stöd för det.
5. **Klassificera försiktigt.** Konvertera bara entydiga valörer. Om flera källrader ger olika klasser för samma identifierade art ska konflikten redovisas och inte lösas med "senaste raden vinner". Kompletteringsposter utan ny klass ska sakna `breeding_class` helt.
6. **Skriv JSON.** Använd formatversion 1 och giltiga fältnamn. Lägg helst relaterade grupper i samma fil, men **högst 100 artposter per fil**. Skapa balanserade filer snarare än en fil per liten inkommande batch; undvik att skapa identiska arter i flera filer.
7. **Validera innan commit.** Kontrollera giltig JSON, `version: 1`, objektlista, obligatoriska fält, tillåtna klasser, högst 100 poster, inga dubbletter inom eller mellan nya filer och ingen oavsiktlig omklassning av tidigare importerade arter. Jämför före/efter-antal vid omstrukturering, och säkerställ att synonymer, geografier, länkar och C/L/CW-nummer följer med.
8. **Leverera via PR.** Beskriv filer och antal poster, vad som slogs ihop, vad som undantogs, motstridiga namn/valörer och vad som återstår för manuell kontroll. Importera **inte i produktionsdatabasen** som del av filgenereringen. Kör inte projektets testsvit om användaren bett att den inte ska köras; påminn om alla tester och provimport före merge.

## Outputformat (alltid)

```json
{
  "version": 1,
  "species": [
    {
      "genus": "Hypancistrus",
      "scientific_name": "zebra",
      "breeding_class": "gold",
      "swedish_names": ["Zebramal"],
      "english_names": ["Zebra pleco"],
      "scientific_synonyms": [],
      "geographies": ["Sydamerika"],
      "cl_number": "L046",
      "links": [
        {
          "url": "https://example.org/species",
          "source_name": "Exempelkälla",
          "title": "Hypancistrus zebra"
        }
      ]
    }
  ]
}
```

Detta är en **schemaillustration**, inte faktiska verifierade uppgifter eller en verklig källa. Bara `genus` och `scientific_name` är alltid obligatoriska. När en **ny** art skapas krävs dessutom `breeding_class` och minst ett värde i `swedish_names`. När ett svenskt namn inte finns i källan kan hela vetenskapliga namnet användas som neutralt primärnamn; rapportera detta i sammanställningen. Utelämna okända frivilliga fält i stället för att fylla i på måfå.

`scientific_name` ska innehålla artdelen, **inte** släktet; `scientific_synonyms` innehåller däremot fullständiga vetenskapliga namn. `geographies` är en lista över de platser/regioner källan faktiskt uppger. `links` ska bara innehålla verkliga, relevanta URL:er, aldrig exempel-URL:en ovan.

### Valörer

När källan använder de tidigare bokstavsbeteckningarna:

| Källvärde | `breeding_class` | Poäng |
| --- | --- | ---: |
| B | `bronze` | 1 |
| S | `silver` | 3 |
| G | `gold` | 7 |
| E | `elite` | 7 |
| "Valör saknas" / uttryckligen "Ej bedömd" | `unrated` | 1 (preliminärt) |

`H`, `RÖDLIST`, `Avvakta`, `-`, tomma eller andra okända markeringar **får inte automatiskt** översättas till `unrated`. Avskilj dem i en granskningslista tills deras betydelse är klarlagd. Den numeriska poängkolumnen i källan är inte ett separat JSON-fält; det är **klassen** som importeras. Verifiera vid behov aktuell poängmappning i `breedings/scoring.py`.

Viktigt: Ett uttryckligen angivet `breeding_class` **ändrar klassen för en befintlig art** när importen körs. Undvik därför att lägga in `unrated` för redan klassade arter bara för att en ny rad saknar klassning.

### Vetenskapliga namn, nummer och varianter

- Dela `Hypancistrus zebra` till `genus: "Hypancistrus"`, `scientific_name: "zebra"`.
- Lägg exempelvis `L 046`, `l046`, `CW 062` i `cl_number` som `L046` respektive `CW062`. Normalisera blanksteg och versaler; **behåll ledande nollor**.
- Om en rad heter `Ancistrus sp. L519`, använd `genus: "Ancistrus"`, `scientific_name: "sp."` och `cl_number: "L519"`. Skriv inte numret enbart som del av artnamnet.
- Populationer och lokalformer, t.ex. `Aphyosemion ocellatum "Ngouambanga"`, är inte automatiskt nya arter. Bevara deras beteckning i ett lämpligt alternativt namn när de hör till samma art och klass, eller markera som osäker om klass/identitet skiljer sig.
- Äldre vetenskapliga kombinationer kan läggas i `scientific_synonyms` **efter säker identitetskontroll**. Ett populärnamn är inte en vetenskaplig synonym.
- Generiska `spp.`-samlingsposter är inte enskilda arter. Rader som endast säger `sp.` **utan** identifierare kan vara tvetydiga: identifiera inte en ny art genom gissning.
- Stavfel får rättas när korrigeringen är säker, med originalformen noterad vid behov. Ändra inte taxonomisk identitet enbart för att ett nyare namn verkar rimligt.

### Dubbletter och uppdateringar

Samma artidentifierare får inte förekomma flera gånger i nya filer. Om en art redan förekommer i andra importfiler, gör hellre en välmotiverad kompletteringspost **utan** `breeding_class`, eller uppdatera den befintliga filen/namnposten. Kontrollera om motstridiga källuppgifter gäller olika L/C/CW-nummer, olika lokalformer eller verkligt olika arter.

För flera filer, använd namn som tydligt visar gruppen och vid behov nummer, exempelvis `pansarmalar_01_artimport.json`, `pansarmalar_02_artimport.json`. Följ redan etablerad namnkonvention i repo. Sortering efter släkte/art/nummer kan underlätta manuell granskning.

## Kvalitetsrapport

Avsluta med en kort rapport som anger:

- Antal källrader, skapade/kompletterade JSON-poster och filer, med antal poster per fil (alla högst 100).
- Antal sammanlagda/dubbla rader, exkluderade poster och rader för manuell kontroll, med skäl.
- Osäkra taxonomiska namn, oeniga odlingsklasser och eventuella C/L/CW-kollisioner.
- Branch, PR-länk och vad som faktiskt verifierats. Redovisa om tester eller provimport **inte** har körts.

## Gränser

Denna skill skapar och granskar importfiler. Ändra inte Django-modeller, importmotor, datamigreringar eller annan applikationskod som bieffekt. Om aktuellt importformat inte kan uttrycka en källuppgift: dokumentera begränsningen och föreslå ett **separat ärende** i stället för en oombedd kodändring.

## Exempel på användaruppdrag

> "Skapa importfiler av den bifogade listan. Det är CSV den här gången. Lägg till nya arter i en branch med PR, högst 100 arter per fil, och rapportera oklassificerade och osäkra rader."

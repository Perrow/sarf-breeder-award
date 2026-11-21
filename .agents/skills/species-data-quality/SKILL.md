---
name: species-data-quality
description: "Hämta tio slumpmässiga arter med databrister från Odlingskampanjen, kontrollera FishBase/NCS Artregister och andra källor och skapa granskbara kompletteringar av artdata, vetenskapliga synonymer, vanliga namn, geografier och källänkar via importfil och pull request."
---

# Komplettera artregistret från Datakvalitet

## Förutsättning och datakälla

1. Hämta **live** JSON från `https://odlingskampanjen.se/api/species/data-quality/random/` med GET. Svaret är en ögonblicksbild och innehåller högst tio slumpmässiga arter med `quality_score >= 1`.
2. Om endpointen inte är driftsatt, svarar med fel eller inte kan hämtas: **stoppa**. Använd inte gissade arter eller exempeldata som ersättning. Endpointen kan bara läsas; den uppdaterar inte databasen.
3. Arbeta i `Perrow/sarf-breeder-award` via separat branch och PR mot `main`. **Skriv aldrig direkt till produktionsdatabasen**, och gör inga commits till `main`.
4. Läs alltid aktuell `taxonomy/species_import.md`, `taxonomy/species_import.py` och `.agents/skills/species-import/SKILL.md` **innan** en fil skapas. Den befintliga artimportören är det enda stödda skrivgränssnittet.

## Svarsformat (översikt)

`{"count": 1, "species": [{"id": 123, "genus": "Genus", "scientific_name": "species", "full_scientific_name": "Genus species", "cl_number": "", "swedish_name": "Genus species", "english_name": "", "geographies": [], "scientific_synonyms": [], "common_name_synonyms": [], "links": [], "quality_score": 4, "missing": {"swedish_name": true, "english_name": true, "geography": true, "links": true}}]}`

Detta är **endast ett schemaexempel**; det innehåller inga verifierade artuppgifter.

## Arbeta art för art

1. Sök efter det **exakta** fullständiga vetenskapliga namnet och ta hänsyn till `cl_number` och befintliga synonymer. För `sp.`/L-/C-/CW-poster: välj aldrig en källa som handlar om en annan nummeridentifierare.
2. Undersök i första hand **FishBase** (`fishbase.se`), **NCS Artregister** (`ciklid.org`) när relevant och andra tillförlitliga taxonomiska eller akvaristiska källor (t.ex. Catalog of Fishes, GBIF, seriösa artregister eller publicerade artbeskrivningar). Sök endast på tillgängligt publicerat material, respektera licensvillkor och åtkomstbegränsningar. Hitta inte på direkta artlänkar eller citeringar.
3. För varje `missing`-flagga med `true`: försök hitta svensk benämning, engelskt namn, geografisk utbredning respektive minst en direktlänk till en relevant källa. Fullständigt vetenskapligt namn är **inte** ett nytt svenskt trivialnamn. Om inget svenskt namn går att belägga, behåll det nuvarande namnet oförändrat.
4. Även om en flagga är `false`, kontrollera om en **säker vetenskaplig synonym**, alternativa trivialnamn, mer precis geografi eller kompletterande relevanta länkar finns. Lägg bara till sådant som faktiskt stöds av källor. Skilj giltiga synonymer från felstavningar, felidentifieringar, homonymer och accepterade namn; kontrollera namnens artidentitet.
5. Dokumentera källa och dess exakta URL **för varje föreslagen ändring**, samt konflikter och kvarvarande osäkerheter. Om källorna motsäger varandra, avstå från automatisk uppdatering och markera posten för manuell granskning.
6. Jämför med `data/species/` i aktuell branch och med befintliga värden från endpointen. Undvik att skapa dubbletter eller skriva över bättre uppgifter. Lämna `breeding_class` utanför kompletteringsposter: den får **inte** ändras som bieffekt. Ändra inte identifierande släkte, artepitet eller C/L-nummer automatiskt.
7. Skriv verifierade kompletteringar i `data/species/` med formatversion 1. Använd `genus`, `scientific_name` och vid behov `cl_number` för exakt träff; fyll endast relevanta värden i `swedish_names`, `english_names`, `geographies`, `scientific_synonyms`, `links` och eventuella synonymer för populärnamn enligt importkontraktet. Högst **100 artposter per fil**. Testa att JSON-format och identiteter stämmer innan PR.
8. Skapa PR till `main` med källförteckning per art, sammanfattning av faktiskt tillagda fält, eventuella kontroverser och instruktion om granskning/import. **Ingen import i produktion sker genom att skillen körs.** Återkör endpointen före ny batch för uppdaterat urval.

## Viktiga gränser

- Endpointens `id` är en referens för granskning, **inte** en importnyckel. Det befintliga JSON-importformatet matchar på släkte, artnamn och valfritt C/L-nummer; var särskilt försiktig vid namn- och nummerkonflikter.
- Geografier i källor bör återges korrekt (t.ex. avrinningsområde kontra specifik flod), utan överdrivet precisa påståenden.
- Varje extern länk ska vara en verklig, verifierad art-/taxonsida och ha korrekt `source_name` och gärna `title`. Länka inte bara en generell startsida för att förbättra poängen.
- Importeraren kan bevara tillagda uppgifter men kan även uppdatera existerande fält. Läs implementeringen och säkerställ att en komplettering inte raderar eller försämrar värden.
- Kör inte projektets testsvit om användaren uttryckligen bett att den inte ska köras. Påminn om samtliga tester och provimport före merge.

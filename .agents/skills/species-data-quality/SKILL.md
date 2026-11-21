---
name: species-data-quality
description: "Hämta tio slumpmässiga arter med databrister från Odlingskampanjen, kontrollera FishBase/NCS Artregister och andra källor och skapa granskbara kompletteringar av artdata, vetenskapliga synonymer, vanliga namn, geografier och källänkar via importfil och pull request."
---

# Komplettera artregistret från Datakvalitet

## Förutsättning och datakälla

1. Hämta **live** JSON från `https://odlingskampanjen.se/api/species/data-quality/random/` med GET. Svaret är en ögonblicksbild och innehåller högst tio slumpmässiga arter med `quality_score >= 1`.
2. Om endpointen inte är driftsatt, svarar med fel eller inte kan hämtas: **stoppa**. Använd inte gissade arter eller exempeldata som ersättning. Endpointen kan bara läsas; den uppdaterar inte databasen.
3. Arbeta i `Perrow/sarf-breeder-award` via **en återanvänd, öppen PR** mot `main`, enligt arbetsflödet nedan. Skapa inte en ny PR vid varje körning. **Skriv aldrig direkt till produktionsdatabasen**, och gör inga commits till `main`.
4. Läs alltid aktuell `taxonomy/species_import.md`, `taxonomy/species_import.py` och `.agents/skills/species-import/SKILL.md` **innan** en fil skapas. Den befintliga artimportören är det enda stödda skrivgränssnittet.

## Återanvänd en Datakvalitet-PR (obligatoriskt vid varje körning)

**Innan du skapar en branch, committar någon fil eller öppnar en PR:**

1. Hämta **samtliga öppna pull requests** för `Perrow/sarf-breeder-award` från GitHub (använd paginering tills alla har lästs in). Begränsa till PR:er vars **basbranch är `main`** och vars **titel börjar med exakt `Datakvalitet`**. Att ordet förekommer mitt i titeln räcker inte. Undersök även att head-branchen tillhör samma repository och är skrivbar.
2. **Exakt en match:** återanvänd den befintliga PR:ens `head.ref` och aktuella head-commit. Hämta och läs innehållet i dess branch, framför allt `data/species/`, innan du skapar eller ändrar filer. **Skapa varken ny branch eller ny PR.** Ändra och pusha bara till den identifierade branchen; behåll tidigare commits och filer.
3. **Ingen match:** skapa en ny branch från aktuell `main` för artkompletteringar. När verifierade filer finns, öppna **en** PR till `main` med titel som **börjar med `Datakvalitet`**, exempelvis `Datakvalitet – kompletteringar av artregistret`. Använd därefter samma PR i följande körningar.
4. **Flera matchningar:** stoppa innan filändringar eller PR-skapande. Redovisa nummer och URL:er så att en enda huvud-PR kan väljas; slå inte automatiskt ihop branchar och välj inte slumpmässigt.
5. Om den funna PR:en är stängd/mergad, har fel basbranch eller head-branchen inte kan uppdateras: kontrollera aktuellt läge på nytt. Behandla aldrig en stängd PR som öppen; skapa inte en parallell PR på antaganden. Förklara hindret vid oklarheter.
6. **Äldre PR-titlar:** tidigare kompletterings-PR:er kan ha `Datakvalitet` längre in i titeln. De räknas **inte** som matchningar enligt prefixregeln. Byt titel på den PR som användaren valt som huvud-PR så att den börjar med `Datakvalitet` och se till att det finns **bara en** öppen prefixmatch. Migrera eller stäng aldrig andra äldre PR:er automatiskt.

**Vid fortsatt arbete i samma PR:**

- Jämför det nya urvalet både med endpointens befintliga data och med **samtliga tidigare kompletteringar på PR-branchen** (inklusive redan skapade JSON-filer). Undvik att lägga samma art eller uppgift i flera filer. Uppdatera befintliga artposter i lämplig fil när det går; håll varje fil under 100 artposter.
- Synkronisera branchen innan du skriver för att undvika att tidigare ändringar skrivs över. Om en parallell körning har pushat nya commits: hämta om branchen, jämför och applicera din ändring på den nya head-committen. Skriv **aldrig över** någon annans commits eller använd force-push för att lösa en konflikt.
- Efter att ändringarna pushats: **uppdatera beskrivningen på samma PR** med denna körnings arter, källor, tillägg och återstående osäkerheter. Bevara tidigare körningars beskrivningar och källredovisning; lägg till en ny omgång. Kontrollera att PR-numret är oförändrat och att titeln fortfarande börjar med `Datakvalitet`.
- Om en annan körning arbetar samtidigt, eller ändringarna krockar: stoppa och redovisa konflikten i stället för att skapa en alternativ PR.

## Svarsformat (översikt)

`{"count": 1, "species": [{"id": 123, "genus": "Genus", "scientific_name": "species", "full_scientific_name": "Genus species", "cl_number": "", "swedish_name": "Genus species", "english_name": "", "geographies": [], "scientific_synonyms": [], "common_name_synonyms": [], "links": [], "quality_score": 4, "missing": {"swedish_name": true, "english_name": true, "geography": true, "links": true}}]}`

Detta är **endast ett schemaexempel**; det innehåller inga verifierade artuppgifter.

## Arbeta art för art

1. Sök efter det **exakta** fullständiga vetenskapliga namnet och ta hänsyn till `cl_number` och befintliga synonymer. För `sp.`/L-/C-/CW-poster: välj aldrig en källa som handlar om en annan nummeridentifierare.
2. Undersök i första hand **FishBase** (`fishbase.se`), **NCS Artregister** (`ciklid.org`) när relevant och andra tillförlitliga taxonomiska eller akvaristiska källor (t.ex. Catalog of Fishes, GBIF, seriösa artregister eller publicerade artbeskrivningar). Sök endast på tillgängligt publicerat material, respektera licensvillkor och åtkomstbegränsningar. Hitta inte på direkta artlänkar eller citeringar.
3. För varje `missing`-flagga med `true`: försök hitta svensk benämning, engelskt namn, geografisk utbredning respektive minst en direktlänk till en relevant källa. Fullständigt vetenskapligt namn är **inte** ett nytt svenskt trivialnamn. Om inget svenskt namn går att belägga, behåll det nuvarande namnet oförändrat.
4. Även om en flagga är `false`, kontrollera om en **säker vetenskaplig synonym**, alternativa trivialnamn, mer precis geografi eller kompletterande relevanta länkar finns. Lägg bara till sådant som faktiskt stöds av källor. Skilj giltiga synonymer från felstavningar, felidentifieringar, homonymer och accepterade namn; kontrollera namnens artidentitet.
5. Dokumentera källa och dess exakta URL **för varje föreslagen ändring**, samt konflikter och kvarvarande osäkerheter. Om källorna motsäger varandra, avstå från automatisk uppdatering och markera posten för manuell granskning.
6. Jämför med `data/species/` i **den återanvända PR-branchen** (eller i den nya branchen om ingen öppen PR finns), inklusive filer från tidigare körningar, och med befintliga värden från endpointen. Undvik att skapa dubbletter eller skriva över bättre uppgifter. Lämna `breeding_class` utanför kompletteringsposter: den får **inte** ändras som bieffekt. Ändra inte identifierande släkte, artepitet eller C/L-nummer automatiskt.
7. Skriv verifierade kompletteringar i `data/species/` med formatversion 1. Använd `genus`, `scientific_name` och vid behov `cl_number` för exakt träff; fyll endast relevanta värden i `swedish_names`, `english_names`, `geographies`, `scientific_synonyms`, `links` och eventuella synonymer för populärnamn enligt importkontraktet. Högst **100 artposter per fil**. Testa att JSON-format och identiteter stämmer innan PR.
8. Återanvänd och **uppdatera befintlig öppen Datakvalitet-PR**, eller skapa en ny sådan PR **endast om ingen finns**. Beskriv varje omgång med källförteckning per art, faktiskt tillagda fält, kontroverser och instruktion om granskning/import; behåll tidigare omgångars redovisning. **Ingen import i produktion sker genom att skillen körs.** Återkör endpointen före ny batch för uppdaterat urval.

## Viktiga gränser

- Endpointens `id` är en referens för granskning, **inte** en importnyckel. Det befintliga JSON-importformatet matchar på släkte, artnamn och valfritt C/L-nummer; var särskilt försiktig vid namn- och nummerkonflikter.
- Geografier i källor bör återges korrekt (t.ex. avrinningsområde kontra specifik flod), utan överdrivet precisa påståenden.
- Varje extern länk ska vara en verklig, verifierad art-/taxonsida och ha korrekt `source_name` och gärna `title`. Länka inte bara en generell startsida för att förbättra poängen.
- Importeraren kan bevara tillagda uppgifter men kan även uppdatera existerande fält. Läs implementeringen och säkerställ att en komplettering inte raderar eller försämrar värden.
- Kör inte projektets testsvit om användaren uttryckligen bett att den inte ska köras. Påminn om samtliga tester och provimport före merge.
- Avsluta varje körning med **nummer och länk till samma PR**, om en sådan återanvänts, samt antal nytillkomna respektive redan hanterade arter.

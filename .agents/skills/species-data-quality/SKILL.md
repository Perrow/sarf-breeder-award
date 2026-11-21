---
name: species-data-quality
description: "Arbeta systematiskt igenom ogranskade arter från Odlingskampanjen, föra granskningslogg i samma Datakvalitet-PR, prioritera innehållsrika artprofiler hos FishBase och Zoopet och komplettera verifierade namn, geografier och synonymer via JSON-import."
---

# Komplettera artregistret från Datakvalitet

## Förutsättning och datakälla

1. Hämta **live** JSON från `https://odlingskampanjen.se/api/species/data-quality/random/` med GET. Adressen behålls av kompatibilitetsskäl, men urvalet är numera **systematiskt**: högst tio arter per sida (`?page=2` för nästa sida), med störst bristpoäng först och därefter alfabetisk ordning. Endpointen filtrerar bort granskade arter tills planerad omgranskning.
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
- Hämta alltid den senaste versionen av PR-branchen innan du ändrar filer. Bevara tidigare commits, importfiler och granskningslogg. **Ingen parallell körning eller låsmekanism behövs** i nuvarande arbetssätt; använd inte force-push.
- Efter att ändringarna pushats: **uppdatera beskrivningen på samma PR** med denna körnings arter, källor, tillägg och återstående osäkerheter. Bevara tidigare körningars beskrivningar och källredovisning; lägg till en ny omgång. Kontrollera att PR-numret är oförändrat och att titeln fortfarande börjar med `Datakvalitet`.
- Om en ändring ändå krockar med befintliga data: redovisa konflikten i stället för att skapa en alternativ PR.

## Systematisk arbetskö och granskningslogg

**Det här avsnittet är obligatoriskt före varje batch och ska följas även om inga uppgifter hittas.**

1. Hämta först den enda öppna Datakvalitet-PR:en enligt reglerna ovan och läs **alla** `data/species/data_quality_review_log*.json` från dess branch om de finns. Varje fil använder `{"version": 1, "species": [...]}` med en granskningsrad per art. Läs också **övriga tidigare kompletteringsfiler**. Om tidigare omgångar saknar granskningsposter, gå igenom deras källredovisning och efterregistrera en post per faktiskt granskad art i loggen (utan att påstå att ej kontrollerade fält har granskats). Sätt då `not_checked` eller `uncertain` där underlag saknas; markera `manual_review` vid osäker identitet. Gör detta innan du väljer nästa tio. När en ny PR behövs används samma filnamn.
2. Hämta sida 1 från live-endpointen, och fortsätt genom `next_page` tills **tio arter som inte redan finns i granskningsloggen eller pågående kompletteringsfiler** har hittats. Om bara färre finns, ta dessa. **Stoppa när `next_page` är `null`**. Sök i loggen med exakt kombination av `genus`, `scientific_name`, `cl_number` och vid behov API-id för kontroll. Ett högt bristpoängtal är inte anledning att ompröva en redan undersökt art under samma PR.
3. Granska varje utvald art även om inga nya uppgifter hittas. Spara **alltid** ett `quality_review`-objekt i den gemensamma loggfilen:
   - `status: "reviewed"` när källsökningen har slutförts, oavsett om något hittades; `"manual_review"` om osäkerhet behöver mänskligt beslut.
   - `reviewed_at`: dagens datum `YYYY-MM-DD`. Ange `review_again_after` om omgranskning önskas vid annat datum än **365 dagar efter granskningen**. Manuellt flaggade arter får ingen automatisk omgranskning.
   - `fields` ska ha **samtliga fyra nycklar** `swedish_name`, `english_name`, `geography`, `links`. För var och en välj `found`, `not_found`, `uncertain` eller `not_checked`. `found` betyder att en tillförlitlig uppgift finns eller har verifierats; inte att någon godtycklig text fylldes i.
   - `sources`: lista över **verkligt använda och verifierade HTTPS-källor** (inte generiska sökresultat). `notes`: kort dokumentation om kvarvarande luckor, taxonomiska konflikter och varför källor valdes/valdes bort.
   - **Vid `status: "manual_review"` krävs `manual_review_comment`** med en konkret, handlingsbar kommentar för administratören. Ange **befintligt värde/länk**, **föreslagen ändring eller borttagning**, **varför det behövs** och **exakt käll-URL** som stöder förslaget. Exempel: "Länken https://... visar en annan art och bör tas bort; se https://..."; "Nuvarande vetenskapliga namn X verkar ha ersatts av Y enligt https://...; kontrollera taxonomin före namnbyte"; "Befintligt populärnamn A bör eventuellt ersättas av B enligt https://...". Lämna ingen vag kommentar som enbart säger "kontrollera art".
   - **Skilj synonymer från namnbyten**: ett verifierat äldre eller alternativt vetenskapligt namn (även det som används av FishBase när ett annat namn ännu är primärt lokalt) läggs i `scientific_synonyms`; alternativa svenska/engelska namn läggs i `swedish_names`/`english_names` så att de registreras som populärnamnssynonymer. **Skriv dem i artens JSON-komplettering, inte bara i en kommentar.** Efter att varje artpost skapats: kontrollera att varje vetenskapligt namn som nämns som möjligt namnbyte i en kommentar faktiskt finns i `scientific_synonyms` för samma art. Om inte, verifiera och lägg till synonymen, eller ta bort namnbytesförslaget.
   - **FishBase är primär källa för bedömning av accepterat vetenskapligt namn och alternativa vetenskapliga och vanliga namn.** Kontrollera noggrant aktuell accepterad kombination, synonymstatus och rätt artidentitet; vid motstridiga taxonomiska uppgifter, kontrollera även Catalog of Fishes eller primärpublicering och flagga osäkerheten.
   - Om ett nytt **primärt** namn är verifierat: skriv `primary_scientific_name` (fullständigt vetenskapligt namn), `primary_swedish_name` eller `primary_english_name` i artens importpost, med **den gamla identiteten** i `genus`/`scientific_name`/`cl_number`. Importen utför namnbytet och bevarar tidigare primärnamn som synonym; administratören ska inte behöva mata in namnet manuellt. Dokumentera före/efter-värden och exakt FishBase-URL i granskningsloggens `notes` och `sources`, men låt **JSON-fälten** bära själva ändringen.
   - Vid **osäkert eller motstridigt** primärnamnsbyte: **föreslå överhuvudtaget inte namnbyte förrän det alternativa namnet har verifierats som synonym till exakt samma art och lagts i artpostens `scientific_synonyms`**. Ange då även `quality_review.proposed_scientific_name` med exakt samma fullständiga namn, `status: "manual_review"` och en konkret `manual_review_comment` med taxonomisk konflikt och källor. Detta förslag ändrar inte primärnamnet, men synonymen importeras omedelbart. Om synonymidentiteten är osäker: ange inget namnbytesförslag i kommentaren, utan dokumentera enbart att identiteten kräver undersökning. Om en befintlig länk bör tas bort används kommentar, eftersom importen inte tar bort länkar.
4. Loggfilen ska ha **exakt en post per identitet**. Behåll gamla granskningsposter och komplettera med den nya omgångens poster; skriv inte över loggen med bara dagens batch. Ändra inte redan behandlade arter utan uttrycklig omgranskning. Håll högst 100 artposter i varje importfil; vid större logg dela i numrerade filer och läs samtliga (använd då `data_quality_review_log_01.json`, `_02.json` osv. och följ samma regler).
5. Lägg verifierade nya artuppgifter i ordinarie kompletteringsfil(er), separerat från granskningsloggen. Vid import applicerar importmotorn loggens `quality_review` på respektive **befintliga** art. Den kan importeras separat och återimporteras säkert. Enbart loggning betyder alltså inte att nya namn behöver hittas.
6. Redovisa batchens **antal granskade arter**, antal med nya uppgifter, antal utan hittade uppgifter och antal som kräver manuell granskning. Vid nästa körning fortsätt där den gemensamma loggen slutade. Om endpointen inte längre har några kvalificerade arter, rapportera att arbetskön är tom.

### Exempel på granskningspost (endast schema)

```json
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
    "sources": [],
    "notes": "Exempelinnehåll, inte verklig granskning."
  }
}
```

**Driftsättningsordning:** merge/deploy applikationsändring och kör migreringen före import av loggar med `quality_review`. Fram till dess hålls statusen i PR-branchen, inte i databasen.

## Välj externa artlänkar efter **källkvalitet, inte antal**

- **För ciklider är NCS Artregister (`ciklid.org`) den högst prioriterade källan** när den har en korrekt, relevant artsida. Undersök NCS först och prioritera dess verifierade, innehållsrika artprofil framför FishBase, Zoopet och andra källor. För övriga fiskar prioriteras **FishBase och Zoopet** när de har verkliga, relevanta och innehållsrika artprofiler. Kontrollera alltid själva sidan och exakt artidentitet: en felaktig, missvisande eller innehållsfattig träff ska väljas bort oavsett källa.
- Om den prioriterade källan saknar en relevant eller användbar artsida: leta efter andra **utförliga, tillförlitliga** artpresentationer, exempelvis FishBase, Zoopet, vetenskapliga artbeskrivningar, seriösa artregister, Catalog of Fishes eller välunderbyggda specialistkällor. En källa kan vara bra för taxonomisk synonymi men svag för akvariehållning, eller tvärtom.
- **Föredra artlänkar där sidan innehåller konkret information om hur arten odlas i akvarium**: exempelvis lekbeteende, hur lek stimuleras, vattenvärden och temperatur vid odling, leksubstrat, föräldravård samt skötsel och utfodring av ägg eller yngel. Kontrollera att odlingsinformationen verkligen avser exakt rätt art eller dokumenterad C/L-variant; anta inte att generella råd för släktet gäller arten.
- Vid jämförbar tillförlitlighet och korrekt artidentitet ska en **utförlig, verifierbar odlingsbeskrivning väga tyngre** än en sida som huvudsakligen innehåller systematik, utbredning eller allmän akvarieskötsel. För ciklider ska NCS Artregister undersökas och ges första prioritet, men en annan källa kan väljas om NCS saknar rätt art eller artspecifik, användbar information. För övriga arter gäller motsvarande prioritet för FishBase och Zoopet. Välj alltid en bättre belagd och mer användbar odlingsbeskrivning framför en tunn eller felaktig profil. Hitta inte på odlingsråd när de saknas.
- Bedöm även identitet, taxonomisk precision, täckning av naturlig utbredning och namn, vetenskapliga referenser, uppdateringsgrad och hur mycket faktisk information **artens egen sida** innehåller. En taxonomisk databas som enbart ger namnet är ibland en nödvändig källa för synonymi men inte en heltäckande artprofil.
- Spara hellre **en eller två starka kompletterande artlänkar** än många svaga. Fler länkar förbättrar inte kvaliteten i sig. Behåll redan etablerade korrekta länkar; om en länk verkar felaktig eller bör tas bort ska den i stället beskrivas i `manual_review_comment` med `status: "manual_review"`.
- Spara bara **direktlänkar till relevant artinformation** med korrekt `source_name` och `title`; aldrig generiska startsidor, sökresultat, automatiskt konstruerade URL:er eller sidor som inte går att verifiera. Dokumentera varför en vald källa är relevant.
- Komplettera även verifierade vetenskapliga synonymer och namn/geografier från relevanta källor, utan att föra över ogrundade formuleringar eller låta länkar styra odlingsklass eller taxonomisk identitet.

## Svarsformat (översikt)

`{"count": 1, "species": [{"id": 123, "genus": "Genus", "scientific_name": "species", "full_scientific_name": "Genus species", "cl_number": "", "swedish_name": "Genus species", "english_name": "", "geographies": [], "scientific_synonyms": [], "common_name_synonyms": [], "links": [], "quality_score": 4, "missing": {"swedish_name": true, "english_name": true, "geography": true, "links": true}}]}`

Detta är **endast ett schemaexempel**; det innehåller inga verifierade artuppgifter.

## Arbeta art för art

1. Sök efter det **exakta** fullständiga vetenskapliga namnet och ta hänsyn till `cl_number` och befintliga synonymer. För `sp.`/L-/C-/CW-poster: välj aldrig en källa som handlar om en annan nummeridentifierare.
2. Undersök i första hand **FishBase** (`fishbase.se`), **NCS Artregister** (`ciklid.org`) när relevant och andra tillförlitliga taxonomiska eller akvaristiska källor (t.ex. Catalog of Fishes, GBIF, seriösa artregister eller publicerade artbeskrivningar). Sök endast på tillgängligt publicerat material, respektera licensvillkor och åtkomstbegränsningar. Hitta inte på direkta artlänkar eller citeringar.
3. För varje `missing`-flagga med `true`: försök hitta svensk benämning, engelskt namn, geografisk utbredning respektive minst en direktlänk till en relevant källa. Fullständigt vetenskapligt namn är **inte** ett nytt svenskt trivialnamn. Om inget svenskt namn går att belägga, behåll det nuvarande namnet oförändrat.
4. Även om en flagga är `false`, kontrollera om en **säker vetenskaplig synonym**, alternativa trivialnamn, mer precis geografi eller kompletterande relevanta länkar finns. Lägg bara till sådant som faktiskt stöds av källor. Skilj giltiga synonymer från felstavningar, felidentifieringar, homonymer och accepterade namn; kontrollera namnens artidentitet.
5. Dokumentera källa och dess exakta URL **för varje föreslagen ändring**, samt konflikter och kvarvarande osäkerheter. Om källorna motsäger varandra, avstå från automatisk uppdatering och markera posten för manuell granskning.
6. Jämför med `data/species/` i **den återanvända PR-branchen** (eller i den nya branchen om ingen öppen PR finns), inklusive filer från tidigare körningar, och med befintliga värden från endpointen. Undvik dubbletter och försämringar. Lämna `breeding_class` utanför kompletteringsposter. Ändra inte C/L-nummer; vetenskapligt släkte och artepitet får endast ändras via explicit `primary_scientific_name` när ny accepterad kombination har verifierats mot FishBase.
7. Skriv verifierade kompletteringar i `data/species/` med formatversion 1 och **en granskningspost för varje undersökt art i granskningsloggen även om inget nytt hittades**. Använd `genus`, `scientific_name` och vid behov `cl_number` för exakt träff; fyll relevanta värden i `swedish_names`, `english_names`, `geographies`, `scientific_synonyms`, `links` samt vid verifierade namnbyten `primary_scientific_name`/`primary_swedish_name`/`primary_english_name`. Högst **100 artposter per fil**. Testa att JSON-format och identiteter stämmer innan PR.
8. Återanvänd och **uppdatera befintlig öppen Datakvalitet-PR**, eller skapa en ny sådan PR **endast om ingen finns**. Beskriv varje omgång med källförteckning per art, faktiskt tillagda fält, kontroverser och instruktion om granskning/import; behåll tidigare omgångars redovisning. **Ingen import i produktion sker genom att skillen körs.** Återkör endpointen före ny batch för uppdaterat urval.

## Viktiga gränser

- Endpointens `id` är en referens för granskning, **inte** en importnyckel. Det befintliga JSON-importformatet matchar på släkte, artnamn och valfritt C/L-nummer; var särskilt försiktig vid namn- och nummerkonflikter.
- Geografier i källor bör återges korrekt (t.ex. avrinningsområde kontra specifik flod), utan överdrivet precisa påståenden.
- Varje extern länk ska vara en verklig, verifierad art-/taxonsida och ha korrekt `source_name` och gärna `title`. Länka inte bara en generell startsida för att förbättra poängen.
- Importeraren kan bevara tillagda uppgifter men kan även uppdatera existerande fält. Läs implementeringen och säkerställ att en komplettering inte raderar eller försämrar värden.
- Kör inte projektets testsvit om användaren uttryckligen bett att den inte ska köras. Påminn om samtliga tester och provimport före merge.
- Avsluta varje körning med **nummer och länk till samma PR**, om en sådan återanvänts, samt antal nytillkomna respektive redan hanterade arter. Rapportera även antalet granskningsposter, antal utan fynd och väntande manuella beslut.

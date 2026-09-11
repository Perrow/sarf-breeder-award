# Systemadministratörens manual

Den här manualen beskriver hur systemadministrationen i **Odlingskampanjen** används. Den omfattar både Djangos inbyggda administrationsfunktioner och de funktioner som har byggts särskilt för systemet.

Manualen beskriver **nuvarande funktionalitet i systemet**. Funktioner som ännu bara finns som planerade ärenden beskrivs inte som färdiga funktioner.

## 1. Logga in i administrationen

Django Admin finns under:

```text
/admin/
```

För att kunna logga in i admin behöver en användare normalt ha Djangos flagga **Personalstatus / is_staff** aktiverad.

I systemet räknas en användare som systemadministratör om något av följande gäller:

- användaren är Django-**superuser**, eller
- användaren tillhör gruppen **Systemadministratör**.

En superuser går förbi vanliga Django-behörighetskontroller och ska därför bara användas för personer som verkligen ska ha full åtkomst till hela installationen.

## 2. Djangos användare, grupper och rättigheter

Django har ett inbyggt behörighetssystem med användare, grupper och modellrättigheter. De viktigaste begreppen är:

### Aktiv

Om **Aktiv** är avstängd kan användaren inte logga in. Använd normalt detta för att blockera ett konto i stället för att radera användaren.

### Personalstatus

**Personalstatus** (`is_staff`) avgör om användaren får logga in i Django Admin. Det innebär inte automatiskt att användaren får ändra någonting där; de faktiska rättigheterna styrs separat.

### Superuser-status

**Superuser-status** (`is_superuser`) ger alla Django-rättigheter utan att de behöver tilldelas en och en. Använd den sparsamt.

### Grupper

Django-grupper används för att samla rättigheter. Systemet använder bland annat gruppnamnen:

- `Systemadministratör`
- `Föreningsadministratör`
- `Medlem`

Den nuvarande implementationen av `Föreningsadministratör` är global: en användare i gruppen får administrera de föreningar som användaren är medlem i. Det finns ett separat planerat arbete för att i framtiden göra föreningsadministratörskap specifikt för ett visst medlemskap. Tills dess ska systemadministratörer vara försiktiga med att lägga användare i gruppen `Föreningsadministratör` om de är medlemmar i flera föreningar.

### Individuella rättigheter

Django skapar normalt fyra grundrättigheter per modell:

- visa
- lägga till
- ändra
- ta bort

Rättigheter kan ges direkt till en användare eller via en grupp. Systemet har dessutom viss egen behörighetslogik ovanpå Djangos standardrättigheter, särskilt för föreningar och odlingsregistreringar.

## 3. Användare

Användarmodellen bygger på Djangos standardmodell och innehåller dessutom några profilspecifika fält.

Vanliga Django-fält är bland annat:

- **Användarnamn** – i den här applikationen används normalt e-postadressen som internt användarnamn.
- **Förnamn** och **efternamn** – användarens namn.
- **E-postadress** – användarens e-postadress.
- **Aktiv** – styr om kontot kan användas för inloggning.
- **Personalstatus** – krävs normalt för åtkomst till Django Admin.
- **Superuser-status** – ger fullständig administrativ åtkomst.
- **Grupper** – används för roll- och rättighetstilldelning.
- **Användarrättigheter** – direkta Django-rättigheter för enskild användare.

Systemets egen användarmodell innehåller även:

- **visningsnamn** – namn som kan användas när användarens profilinformation får visas.
- **publikt användarnamn** – ett unikt, frivilligt namn som kan visas offentligt utan att avslöja personuppgifter.
- **ort** – frivillig ortsinformation.
- **profilbild** – URL till profilbild.

Observera att adminformuläret för användare bygger på Djangos standard-`UserAdmin`. Alla projektspecifika profilfält behöver därför inte nödvändigtvis visas i samma formulär som Djangos standardfält.

### Rekommenderad hantering

Radera inte användare i onödan. Odlingsregistreringar refererar till användaren och historik ska normalt bevaras. Om en användare inte längre ska kunna logga in är det säkrare att avmarkera **Aktiv**.

## 4. Föreningar

Modellen **Association / Förening** innehåller grunduppgifter om en förening.

Fälten betyder:

- **Namn** – föreningens namn. Får inte vara tomt eller bara innehålla blanktecken.
- **Organisationsnummer** – frivilligt organisationsnummer.
- **E-post** – föreningens kontaktadress.
- **Telefon** – föreningens telefonnummer.
- **Adress** – gatuadress.
- **Postnummer** – postnummer.
- **Ort** – postort.
- **Beskrivning** – fri text om föreningen.

I listan kan man söka på namn, organisationsnummer, e-post och ort.

Systemadministratörer kan se och administrera alla föreningar.

## 5. Medlemskap

Ett **Membership / Medlemskap** kopplar en användare till en förening. En användare kan vara medlem i flera föreningar, men samma användare kan inte ha två medlemskap i samma förening.

Fälten betyder:

- **Användare** – vilket konto medlemskapet gäller.
- **Förening** – vilken förening användaren är medlem i.
- **Medlemsnummer** – frivilligt medlemsnummer i just den föreningen.
- **Telefon** – föreningsspecifikt telefonnummer om det behövs.
- **Föreningsdata** (`association_data`) – fri föreningsspecifik information om medlemskapet.

Listan visar namn, e-post, telefon, medlemsnummer och förening och kan filtreras per förening.

### Viktigt om föreningsadministratörer

I dagens implementation avgör gruppen `Föreningsadministratör` om en användare är föreningsadministratör. En sådan användare får administrera samtliga föreningar där användaren har ett medlemskap.

Detta är en känd begränsning. Den planerade modellen är att adminrättigheten i framtiden ska ligga på själva medlemskapet, så att en användare kan vara administratör i en förening men vanlig medlem i en annan. Den förändringen är ännu inte implementerad.

## 6. Taxonomi

Taxonomin består huvudsakligen av släkten, arter, artgrupper, geografier, synonymer och externa länkar.

### 6.1 Släkten

Ett **Genus / Släkte** har:

- **scientific_name / vetenskapligt namn** – unikt vetenskapligt släktnamn.
- **is_active / aktiv** – om släktet är aktivt.

Inaktivera hellre äldre eller ogiltiga släkten än att radera dem när de kan behövas för historik.

### 6.2 Artgrupper

En **SpeciesGroup / Artgrupp** används för att gruppera arter och kan byggas på två sätt:

- genom att koppla hela **släkten** till gruppen,
- genom att koppla enskilda **arter** direkt till gruppen.

Fälten är:

- **Namn** – unikt namn på artgruppen.
- **Synlig för användare** – om gruppen ska visas för vanliga användare.
- **Släkten** – alla arter i de valda släktena ingår i gruppen.
- **Arter** – enskilda arter som ska ingå direkt, oberoende av släkte.

En art kan alltså tillhöra en grupp antingen via sitt släkte eller genom en direktkoppling.

### 6.3 Geografier

**Geografi** är en enkel lista över geografiska områden som kan kopplas till arter.

Fält:

- **Namn** – geografins namn, exempelvis `Malawi`, `Sydamerika` eller annat valt område.

Namn är unika utan hänsyn till stora och små bokstäver.

### 6.4 Arter

En **Species / Art** är systemets centrala taxonomiska post.

Fälten betyder:

- **Släkte** – aktuellt vetenskapligt släkte.
- **Artnamn** – den specifika delen av det vetenskapliga namnet. Tillsammans med släktet bildar det fullständiga vetenskapliga namnet.
- **Populärnamn** – primärt svenskt populärnamn.
- **Engelskt namn** – frivilligt primärt engelskt namn.
- **Odlingsklass** – `Brons`, `Silver` eller `Guld`.
- **Geografier** – geografiska områden som arten är kopplad till.
- **Aktiv** – om arten ska kunna användas för nya registreringar.

Kombinationen **släkte + artnamn** måste vara unik.

Artlistan kan bland annat filtreras på aktiv status, odlingsklass, släkte och geografi. Sökningen omfattar aktuellt vetenskapligt namn, populärnamn, engelskt namn och synonymer.

### 6.5 Vetenskapliga synonymer

Vetenskapliga synonymer visas i en separat sektion på artens adminsida. Administratören anger:

- **Släkte**
- **Artnamn**

I databasen lagras de fortfarande som ett komplett vetenskapligt namn. Uppdelningen i två fält är främst för att administrationen ska bli tydligare.

Ett vetenskapligt synonymnamn används till exempel för ett tidigare accepterat namn på samma art.

### 6.6 Populärnamnssynonymer

Populärnamnssynonymer hanteras i en egen sektion och består av alternativa populärnamn för arten.

En synonympost representerar antingen ett vetenskapligt synonymnamn eller ett populärnamn, aldrig båda samtidigt.

### 6.7 Externa artlänkar

En art kan ha externa länkar till tillförlitliga externa informationskällor.

Fälten är:

- **Källa** – namn på webbplats eller organisation.
- **Sidtitel** – frivillig titel på den länkade sidan.
- **URL** – fullständig webbadress.

Samma URL kan bara förekomma en gång per art.

### 6.8 Byta vetenskapligt namn

Det finns stöd för att ändra en arts aktuella vetenskapliga namn utan att skapa en ny artpost.

Det kan göras på två sätt:

1. Ändra släkte och/eller artnamn direkt i artens formulär.
2. Välja en befintlig vetenskaplig synonym i fältet för att göra synonymen till aktuellt vetenskapligt namn.

När en synonym görs till aktuellt namn tas den bort ur synonym-listan och det tidigare aktuella namnet sparas som synonym. Artens identitet och befintliga relationer behålls.

### 6.9 Slå ihop dubblettarter

På artens adminsida finns stöd för att slå ihop en art med en annan art.

Sammanslagningen startas från den **gamla artposten**, alltså den post som ska tas bort. Öppna den gamla arten i admin och välj funktionen **Slå ihop**. Därefter väljer du den **nya artposten** som mål för sammanslagningen. Målarten är den post som ska finnas kvar efter operationen.

Använd funktionen när två artposter egentligen representerar samma art. Den valda målarten behålls och den gamla källarten tas bort.

Vid sammanslagningen flyttas relevanta relationer till målarten, bland annat:

- odlingsregistreringar,
- direkta artgruppskopplingar,
- geografier,
- synonymer,
- externa länkar.

Källartens aktuella vetenskapliga namn bevaras som synonym på målarten när det är relevant.

Det går inte att slå ihop en art med sig själv.

**Kontrollera alltid noggrant vilken art som ska behållas innan sammanslagningen genomförs.** Funktionen påverkar många relationer och källposten raderas efter en lyckad merge.

### 6.10 Importera arter

Artregistret kan importeras från JSON både via management-kommandot och via adminfunktionerna för artimport.

I admin finns också en hjälpsida för importformatet.

Importen är additiv och återanvänder befintliga data där det går. Den är avsedd att kunna köras flera gånger utan att samma poster skapas om och om igen.

Importen kan hantera bland annat:

- släkte,
- artnamn,
- odlingsklass,
- svenska namn,
- engelska namn,
- vetenskapliga synonymer,
- geografier,
- externa länkar enligt det stödda importformatet.

Om en art tidigare haft ett annat vetenskapligt namn kan importen matcha via vetenskaplig synonym. Det aktuella namnet prioriteras framför synonymmatchning.

Vid osäkerhet: använd hjälplänken på importsidan innan en större import görs.

## 7. Odlingsregistreringar

En **BreedingRegistration / Odlingsregistrering** representerar en användares rapporterade odling.

Fälten betyder:

- **Användare** – den användare som registrerat odlingen.
- **Förening** – föreningen som odlingen registreras för.
- **Art** – kopplad art när taxonomin är känd.
- **Föreslaget släkte** – fritextvärde när användaren inte hittade rätt art i registret.
- **Föreslaget artnamn** – fritextvärde för artnamnet.
- **Föreslaget populärnamn** – frivilligt fritextnamn.
- **Taxonomi behöver lösas** – sätts automatiskt när registreringen saknar koppling till en riktig artpost.
- **Odlingsdatum** – datum för odlingen.
- **Beskrivning** – användarens beskrivning av odlingen.
- **Status** – `Utkast`, `Inskickad`, `Godkänd` eller `Avslagen`.
- **Inskickad** – tidpunkt när rapporten skickades in.
- **Godkänd** – tidpunkt när rapporten godkändes.
- **Tilldelad odlingsklass** – den odlingsklass som frystes in vid godkännandet.
- **Tilldelade poäng** – den poäng som tilldelades vid godkännandet.
- **Granskare** – administratören som fattade beslutet.
- **Granskningskommentar** – kommentar från granskaren.

Systemadministratören ändrar normalt inte odlingsregistreringen direkt via Djangos vanliga redigeringsformulär. I stället används de särskilda åtgärderna **Granska** och **Lös taxonomi**.

### 7.1 Lösa taxonomi

Om användaren registrerat en art i fritext markeras registreringen med att taxonomin behöver lösas.

Välj **Lös taxonomi** och koppla registreringen till rätt befintlig art.

Om arten inte finns kan adminflödet länka vidare till att skapa en ny art med delar av användarens fritext förifyllda. När rätt art finns återgår man till registreringen och kopplar den.

Taxonomin måste vara löst innan registreringen kan godkännas eller avslås via granskningsflödet.

### 7.2 Granska odling

Endast registreringar med status **Inskickad** kan granskas.

På granskningssidan väljer administratören:

- **Beslut** – `Godkänn` eller `Avslå`.
- **Granskningskommentar** – frivillig kommentar, högst 2000 tecken.

Vid godkännande hämtas artens aktuella odlingsklass och sparas på registreringen. Poängen blir:

- Brons = 1 poäng
- Silver = 2 poäng
- Guld = 3 poäng

Den tilldelade klassen och poängen lagras på registreringen så att historiska resultat inte ändras bara för att artens klassificering senare ändras.

Vid avslag rensas godkännandetidpunkt, tilldelad klass och poäng.

## 8. Föreningstävling – grundinställningar

Modellen **Inställning för föreningstävling** styr standardbegränsningen för hur många arter inom ett släkte som får räknas per medlem.

Fälten är:

- **Gäller från och med år** – sätts automatiskt till innevarande år när en ny inställning skapas.
- **Standard: max odlingar per medlem och genus** – högsta antal odlingar/arter inom samma släkte som får bidra enligt standardregeln.

Det måste vara minst 1.

Det kan bara finnas en inställning per startår. Äldre års inställningar bevaras för historiska resultat. Bara innevarande års inställning får ändras. Poster går inte att radera via admin.

Om ett senare år saknar en ny inställning används den senast gällande inställningen från tidigare år.

## 9. Föreningstävling – särskilda begränsningar

**Begränsningar för föreningstävling** används för undantag från standardregeln.

Varje regel gäller antingen:

- ett specifikt **släkte**, eller
- en **artgrupp**.

Exakt ett av dessa fält ska vara ifyllt.

Fälten är:

- **Släkte** – släkte som regeln gäller för.
- **Artgrupp** – artgrupp som regeln gäller för.
- **Max odlingar per medlem och år** – hur många som får räknas inom området.
- **Gäller från och med år** – sätts automatiskt till aktuellt år när regeln skapas.

Artgrupper som används i den här typen av regel måste vara genusbaserade. En grupp med direktkopplade arter kan inte användas som tävlingsbegränsning.

Systemet hindrar också överlappande regler där ett släkte både omfattas av en släktregel och samtidigt av en gruppregel.

Precis som grundinställningarna bevaras historiska regler. Bara innevarande års poster får ändras och de kan inte raderas via admin.

## 10. Hur tävlingspoäng räknas

För godkända odlingar används odlingsklassens poäng Brons=1, Silver=2 och Guld=3.

För en medlems vanliga årsresultat räknas bara den bästa godkända odlingen per art.

För föreningstävlingen används dessutom de konfigurerade maxgränserna per släkte eller artgrupp. Systemet försöker räkna de mest värdefulla odlingarna först inom respektive begränsning.

För äldre tävlingsår finns även en inlämningsfrist: en registrering för ett avslutat år måste normalt ha skickats in senast 30 dagar efter årsskiftet för att räknas. Äldre legacy-poster utan `submitted_at` behåller sitt historiska resultat.

## 11. Utmärkelser

Utmärkelsesystemet består av:

- **Utmärkelser**
- **Nivåer**
- **Krav**
- **Bakgrunder**
- **Uppnådda utmärkelser**

Nivåer och krav är avsiktligt gömda från adminmenyn och administreras normalt via respektive utmärkelse och nivå.

### 11.1 Utmärkelse

Fälten är:

- **Namn** – unikt namn på utmärkelsen.
- **Ska uppnås inom kalenderår** – om kraven ska räknas separat för varje kalenderår. Om fältet inte är markerat räknas odlingar över hela användarens historik.
- **Utmärkelsebild** – frivillig overlay-bild.
- **Egen bakgrundsbild** – frivillig bakgrund som gäller just denna utmärkelse.
- **Förhandsvisning** – visar hur bakgrund och overlay kombineras.

Utmärkelsebilden måste:

- vara exakt 200 × 250 pixlar,
- vara PNG,
- innehålla genomskinlighet.

En egen bakgrundsbild måste vara exakt 200 × 250 pixlar.

### 11.2 Nivåer

En utmärkelse kan ha flera nivåer.

Fälten är:

- **Utmärkelse** – vilken utmärkelse nivån hör till.
- **Nivånamn** – exempelvis ett namn på nivån.
- **Beskrivning** – frivillig kort beskrivning.
- **Nivåbild** – frivillig overlay för just nivån; samma bildkrav som andra utmärkelse-overlays gäller.
- **Ordning** – nivåns ordning inom utmärkelsen. Måste vara unik inom samma utmärkelse.

På utmärkelsens sida visas nivåerna kompakt med antal krav och länk till att redigera nivån.

### 11.3 Krav

Krav kopplas till en nivå. Alla krav på nivån måste vara uppfyllda för att nivån ska anses uppnådd.

Kravtyper:

- **Poäng** – kräver minst ett visst antal poäng.
- **Antal odlingar** – kräver minst ett visst antal godkända odlingsregistreringar.
- **Antal arter** – kräver minst ett visst antal unika arter.

Fälten är:

- **Nivå** – nivån kravet tillhör.
- **Kravtyp** – Poäng, Antal odlingar eller Antal arter.
- **Kravvärde** – minsta värde som ska uppnås; måste vara minst 1.
- **Genera** – begränsa kravet till arter inom valda släkten.
- **Artgrupper** – begränsa kravet till valda artgrupper.

Om varken släkten eller artgrupper väljs räknas alla godkända odlingar.

Om flera släkten och/eller artgrupper väljs räcker det att en odling hör till något av de valda taxonomiska områdena för att den ska omfattas av det kravet.

För poängkrav räknas den bästa poängen per unik art inom det aktuella urvalet.

### 11.4 Bakgrunder

**AchievementBackground / Bakgrund** används som standardbakgrund för utmärkelser som inte har en egen bakgrund.

Fälten är:

- **Kalenderår** – vilket år bakgrunden gäller. Lämna tomt för lifetime-bakgrund.
- **Bakgrundsbild** – exakt 200 × 250 pixlar.
- **Färgning** – frivillig färg i formatet `#RRGGBB`, endast för årsbaserade bakgrunder.

Det kan bara finnas en lifetime-bakgrund.

För ett år används den senaste bakgrund vars kalenderår är mindre än eller lika med året. Det gör att en årsdesign kan återanvändas tills en ny version skapas.

Lifetime-bakgrunden får inte ha någon års-färgning.

### 11.5 Uppnådda utmärkelser

**Uppnådda** poster skapas av systemet och är skrivskyddade i admin.

De innehåller bland annat:

- användare,
- nivå,
- sparat utmärkelsenamn,
- sparat nivånamn,
- sparad nivåbeskrivning,
- kalenderår för årsbaserade utmärkelser,
- tidpunkt då posten skapades.

De sparade namnen gör att viss historisk information finns kvar även om definitionen av en utmärkelse senare ändras.

Administratören ska inte skapa, ändra eller radera dessa poster manuellt.

### 11.6 Granska utmärkelsen på nytt

På en utmärkelses adminsida finns en funktion för att **granska/revalidera utmärkelsen**.

Den går igenom befintliga godkända odlingar och jämför dem med utmärkelsens nuvarande regler. Systemet kan då:

- ta bort tidigare utdelningar som inte längre uppfyller kraven,
- skapa utdelningar som nu ska finnas.

Använd funktionen när reglerna för en befintlig utmärkelse har ändrats och historiken behöver räknas om.

Var försiktig: en revalidering kan både skapa och ta bort användares uppnådda utmärkelser.

## 12. Rekommenderade arbetsrutiner för systemadministratörer

### Ändra hellre status än att radera historiska objekt

Arter och släkten har aktiva/inaktiva flaggor just för att historiska registreringar ska kunna behålla sina referenser. Inaktivera därför normalt gamla taxonomiska poster i stället för att radera dem.

### Kontrollera taxonomin före merge

Sammanslagning av arter är avsedd för riktiga dubbletter och påverkar många relationer. Kontrollera namn, synonymer, länkar och odlingshistorik innan operationen genomförs.

### Ändra inte historiska tävlingsregler i efterhand

Tävlingsinställningar och specialgränser är årsversionsbaserade. Skapa en ny regel för innevarande år i stället för att försöka skriva om historiska regler.

### Revalidera utmärkelser efter regeländringar

Om krav eller nivåer ändras kan historiskt utdelade utmärkelser behöva räknas om. Använd utmärkelsens revalideringsfunktion medvetet efter sådana förändringar.

### Ge minsta nödvändiga rättighet

Använd grupper och Django-rättigheter för att undvika att ge fler privilegier än en person behöver. `is_superuser` bör reserveras för ett mycket litet antal tekniska/systemansvariga.

## 13. Snabbguide

| Uppgift | Var i admin |
|---|---|
| Skapa eller redigera förening | Associations → Associations |
| Hantera medlemskap | Associations → Memberships |
| Hantera användare och grupper | Authentication/Users/Groups i Django Admin |
| Lägga till släkte | Taxonomy → Genera |
| Hantera artgrupper | Taxonomy → Artgrupper |
| Hantera geografier | Taxonomy → Geografier |
| Lägga till eller ändra art | Taxonomy → Arter |
| Hantera synonymer | På artens redigeringssida |
| Hantera externa artlänkar | På artens redigeringssida |
| Importera artregister | Taxonomy → Arter → Importera arter |
| Byta aktuellt vetenskapligt namn | På artens redigeringssida |
| Slå ihop dubblettarter | Öppna den gamla arten → Slå ihop → välj den nya arten som mål |
| Lösa fritexttaxonomi | Odlingsregistreringar → Lös taxonomi |
| Godkänna/avslå odling | Odlingsregistreringar → Granska |
| Ställa standardgräns för föreningstävling | Inställningar för föreningstävling |
| Skapa specialgräns för släkte/artgrupp | Begränsningar för föreningstävling |
| Skapa utmärkelse | Utmärkelser → Utmärkelser |
| Hantera nivåer | På utmärkelsens sida |
| Hantera krav | Via respektive nivå |
| Hantera bakgrunder | Utmärkelser → Bakgrunder |
| Räkna om en utmärkelse | På utmärkelsens sida → revalidera/granska på nytt |
| Se utdelade utmärkelser | Utmärkelser → Uppnådda |

## 14. När manualen ska uppdateras

Manualen bör uppdateras när:

- nya adminfunktioner läggs till,
- fält får ny innebörd,
- behörighetsmodellen ändras,
- tävlingsreglerna förändras,
- utmärkelsesystemet får nya kravtyper eller presentationsregler.

Särskilt den planerade förändringen av föreningsadministratörskap behöver dokumenteras här när den implementeras, eftersom nuvarande gruppbaserade beteende då ska ersättas av en medlemskapsspecifik behörighet.

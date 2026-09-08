# Manuella webbläsartester

Det här dokumentet är en praktisk, inte heltäckande, checklista för att manuellt verifiera de funktioner som hittills finns i Odlingskampanjen.

## Förberedelser

1. Hämta aktuell branch och installera beroenden.
2. Kör migrationerna:
   ```bash
   python manage.py migrate
   ```
3. Skapa en superuser om du inte redan har en:
   ```bash
   python manage.py createsuperuser
   ```
4. Starta applikationen:
   ```bash
   python manage.py runserver
   ```
5. Öppna `http://127.0.0.1:8000/`.

För vissa tester behövs flera användare och föreningar. Det är enklast att skapa grunddata via Django Admin.

---

## 1. Startsida och grundlayout

### 1.1 Startsida som utloggad

- Öppna startsidan utan att vara inloggad.
- Kontrollera att rubriken **Odlingskampanjen** visas.
- Kontrollera att introduktionstexten om odling, kunskapsinsamling och SARF-anslutna föreningar visas.
- Kontrollera att länken till SARF:s Odlingskampanj öppnas i ny flik.
- Kontrollera att navigationen visar **Logga in** och **Skapa konto**.
- Minska webbläsarfönstret till mobilbredd och kontrollera att sidan fortfarande är lättläst och att navigationen går att öppna.

Förväntat resultat: sidan är responsiv, på svenska och utan trasiga länkar eller överlappande innehåll.

---

## 2. Registrering, inloggning och utloggning

### 2.1 Skapa konto

- Klicka **Skapa konto**.
- Registrera en ny användare med namn, unik e-postadress och giltigt lösenord.
- Kontrollera att du blir inloggad och hamnar på kontosidan.

Förväntat resultat: kontot skapas och e-postadressen används för inloggning.

### 2.2 Ogiltig e-post

- Försök registrera ett konto med exempelvis `inte-en-epost`.

Förväntat resultat: formuläret avvisas med ett begripligt svenskt felmeddelande.

### 2.3 Dubblett av e-post

- Försök registrera ytterligare ett konto med samma e-postadress, gärna med annan kombination av stora/små bokstäver.

Förväntat resultat: kontot skapas inte och ett tydligt felmeddelande visas.

### 2.4 Svagt/ogiltigt lösenord

- Försök registrera ett konto med exempelvis ett enbart numeriskt och enkelt lösenord.

Förväntat resultat: Djangos lösenordsregler stoppar registreringen.

### 2.5 Logga ut och in

- Logga ut.
- Logga in igen med e-postadress och lösenord.
- Försök också med fel lösenord.

Förväntat resultat: korrekt lösenord loggar in, fel lösenord ger svenskt felmeddelande.

---

## 3. Användarprofil

### 3.1 Visa och ändra egen profil

- Logga in som vanlig användare.
- Öppna **Konto**.
- Ändra visningsnamn och ort.
- Ange en giltig bild-URL som profilbild.
- Spara.
- Ladda om sidan.

Förväntat resultat: värdena sparas och profilbilden visas om URL:en är åtkomlig.

### 3.2 Ogiltig profilbilds-URL

- Ange `inte-en-url` som profilbild.

Förväntat resultat: formuläret avvisas med ett svenskt URL-fel.

### 3.3 Tomt visningsnamn

- Ange bara blanksteg som visningsnamn och spara.

Förväntat resultat: ändringen avvisas.

### 3.4 Försök ändra annan användare

- Med utvecklarverktyg eller genom att manipulera formulärdata, lägg till ett godtyckligt `user_id` för en annan användare när den egna profilen sparas.

Förväntat resultat: endast den inloggade användarens profil ändras.

---

## 4. Lösenordsåterställning

Standard i lokal utveckling är console-backend för e-post. Själva återställningsmailet skrivs därför i terminalen där `runserver` körs.

### 4.1 Begär återställning

- Logga ut.
- Öppna lösenordsåterställningen från inloggningssidan.
- Ange e-postadressen till ett befintligt konto.
- Skicka formuläret.

Förväntat resultat: sidan säger att ett mail kan ha skickats utan att avslöja om adressen finns registrerad.

### 4.2 Använd återställningslänk

- Kopiera länken från mailet i terminalen.
- Öppna länken i webbläsaren.
- Ange ett nytt giltigt lösenord.
- Logga därefter in med det nya lösenordet.

Förväntat resultat: lösenordet ändras och det nya lösenordet fungerar.

### 4.3 Återanvänd samma länk

- Försök öppna/använda samma återställningslänk igen efter lyckat lösenordsbyte.

Förväntat resultat: länken är ogiltig/förbrukad och kan inte användas igen.

---

## 5. Django Admin – släkten

Logga in på `/admin/` som superuser.

### 5.1 Skapa och ändra släkte

- Skapa exempelvis `Corydoras`.
- Kontrollera att släktet visas i listan.
- Testa sökning på namnet.
- Markera släktet inaktivt och spara.

Förväntat resultat: släktet finns kvar men visas som inaktivt.

### 5.2 Dubblett

- Försök skapa ytterligare ett släkte med exakt samma vetenskapliga namn.

Förväntat resultat: dubbletten avvisas.

---

## 6. Django Admin – artgrupper

### 6.1 Skapa grupp med helt släkte

- Skapa en artgrupp, exempelvis `Pansarmalar`.
- Lägg till ett eller flera släkten i gruppen.
- Spara och öppna gruppen igen.

Förväntat resultat: släktena ligger kvar i gruppen.

### 6.2 Lägg till enskild art

- Lägg även en enskild art direkt i gruppen.

Förväntat resultat: gruppen kan samtidigt bestå av hela släkten och enskilda arter.

### 6.3 Dold artgrupp

- Skapa en grupp, exempelvis `Pandafiskar`.
- Markera den som dold för användare.
- Kontrollera att adminlistan visar synlighetsstatus och att den går att filtrera på.

Förväntat resultat: gruppen finns kvar och kan administreras trots att den är dold för normala användare.

Obs: det finns ännu ingen fullständig publik artgruppsvy att manuellt kontrollera dold/visad status i. Den delen verifieras därför främst av automatiserade tester tills sådan UI finns.

---

## 7. Django Admin – arter och synonymer

### 7.1 Skapa art

- Skapa ett aktivt släkte först om det behövs.
- Skapa exempelvis:
  - släkte: `Corydoras`
  - artnamn: `panda`
  - populärnamn: `Pandapansarmal`
  - odlingsklass: Silver
- Spara.

Förväntat resultat: arten sparas och visas i artlistan.

### 7.2 Dubblett av släkte + art

- Försök skapa samma kombination av släkte och artnamn igen.

Förväntat resultat: dubbletten avvisas.

### 7.3 Odlingsklass

- Kontrollera att endast Brons, Silver och Guld går att välja.

### 7.4 Inaktiv art

- Markera arten inaktiv och spara.

Förväntat resultat: artposten finns kvar för historisk användning.

### 7.5 Vetenskaplig synonym

- Lägg till ett tidigare vetenskapligt namn, exempelvis `Hoplisoma panda`.
- Spara utan att ändra artens aktuella namn.

Förväntat resultat: synonymen sparas separat och huvudnamnet är oförändrat.

### 7.6 Alternativt populärnamn

- Lägg till ett alternativt populärnamn, exempelvis `Panda cory`.

Förväntat resultat: det alternativa namnet sparas utan att ersätta aktuellt populärnamn.

### 7.7 Sökning i admin

- Sök efter arten med:
  - aktuellt vetenskapligt namn
  - populärnamn
  - tidigare vetenskapligt namn
  - alternativt populärnamn

Förväntat resultat: rätt aktuell artpost hittas.

Obs: den återanvändbara artsökningen för nya odlingsregistreringar finns i domän-/modellagret, men någon färdig publik artväljare för odlingsrapportering finns ännu inte. Full browsertest av filtrering av inaktiva arter blir därför aktuell när registreringsflödet byggs.

---

## 8. Django Admin – föreningar och medlemskap

Förbered tre användare:

- systemadministratör
- föreningsadministratör
- vanlig medlem

Säkerställ också att grupperna `Systemadministratör`, `Föreningsadministratör` och `Medlem` finns efter migration.

### 8.1 Systemadministratör

- Lägg användaren i gruppen **Systemadministratör** och markera användaren som staff.
- Skapa minst två föreningar.
- Logga in i admin med systemadministratören.

Förväntat resultat: användaren kan se och administrera alla föreningar och medlemskap.

### 8.2 Föreningsadministratör

- Lägg en användare i gruppen **Föreningsadministratör**, markera den som staff och skapa ett medlemskap i endast en av föreningarna.
- Logga in i admin som den användaren.

Kontrollera att användaren:

- ser sin egen förening
- inte ser den andra föreningen i listan
- kan ändra sin egen förenings profil
- kan lägga till medlemskap i sin egen förening
- kan ändra och ta bort medlemskap i sin egen förening
- inte kan skapa medlemskap i en annan förening
- inte kan skapa eller ta bort själva föreningsposten

### 8.3 Direkt URL till annan förening

- Kopiera ändrings-URL:en för den andra föreningen när du är systemadministratör.
- Logga sedan in som föreningsadministratör och försök öppna den URL:en direkt.

Förväntat resultat: den andra föreningen kan inte öppnas eller administreras.

### 8.4 Vanlig medlem

- Lägg en användare i gruppen **Medlem**.
- Markera användaren som staff endast för att kunna prova admininloggning.
- Logga in i admin.

Förväntat resultat: användaren saknar administrationsrätt till föreningar och medlemskap.

### 8.5 Medlemsuppgifter

- Skapa eller ändra ett medlemskap.
- Kontrollera namn, e-post, telefonnummer och medlemsnummer i medlemsregistret.
- Försök skapa samma användare som medlem i samma förening två gånger.

Förväntat resultat: uppgifterna kan administreras och dubbelt medlemskap i samma förening avvisas.

---

## 9. Svenskt gränssnitt

Gå igenom de publika sidorna och relevanta adminvyerna.

Kontrollera särskilt:

- navigation
- registrering
- inloggning
- konto/profil
- lösenordsåterställning
- valideringsmeddelanden
- Django Admin

Förväntat resultat: användarsynliga texter är på svenska och inga uppenbart engelska standardtexter dyker upp i normala flöden.

---

## 10. Enkel regression efter framtida merges

När större features mergas bör åtminstone följande snabba kontroll göras manuellt:

1. Startsidan laddas.
2. Ny användare kan registreras.
3. Inloggning och utloggning fungerar.
4. Profil kan ändras.
5. Lösenordsåterställning kan initieras.
6. Superuser kan öppna Django Admin.
7. Släkte, artgrupp, art och synonym kan skapas/ändras.
8. Föreningsadministratör ser endast sin egen förening.

Automatiserade tester ska fortfarande köras i sin helhet före merge:

```bash
python manage.py test -v 2
```

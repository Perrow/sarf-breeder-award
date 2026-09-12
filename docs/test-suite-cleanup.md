# TEST-007 – förenkling av testsviten

Det här svepet prioriterar genomloppstid och underhållbarhet framför bred presentationsregressionstäckning. Tester ska i första hand skydda beteenden som är dyra att upptäcka manuellt: behörighet, dataintegritet, validering, centrala användarflöden och domänregler. Tester som huvudsakligen låser HTML/CSS/Bootstrap-struktur, ordval, ordningsdetaljer eller exakt JavaScript-implementation tas bort även om de i vissa fall kan fånga mindre visuella regressioner.

## Borttagna testtyper

Totalt tas 20 testfall bort i de två svepen.

### Presentation och CSS/Bootstrap

- 4 tester i `users/test_form_layout.py` som verifierade att en CSS-fil gick att hitta och att specifika CSS-/Bootstrap-klasser fanns i login-, registrerings- och lösenordsåterställningsvyer.
- 1 test i `users/test_min_page.py` som verifierade exakt `<title>`, H1, navigationstext och frånvaro av den äldre texten `Mina odlingar`.
- 1 test i `users/test_navigation.py` som endast verifierade Bootstrap-klasser på den anonyma login-länken.
- 1 test i `breedings/test_review_heading.py` som endast verifierade exakt antal H1-element och exakt rubriktext.
- 3 tester i `breedings/test_known_class_in_list.py` som huvudsakligen verifierade exakt markup och klassen `text-body-secondary` för visning av odlingsklass.
- 1 test i `progression/test_admin_menu.py` som låste exakt namn och modellordning i Django Admin-menyn.
- 3 tester borttagna ur `progression/test_achievement_card_interaction.py` som huvudsakligen låste Bootstrap-modalens exakta markup/styling, årvisningens presentation och tom beskrivningspresentation.

### Dubblerande vy- och renderingstester

- 1 test i `breedings/test_review_public_style.py` som verifierade samma centrala granskningsinformation som redan täcks av `breedings/test_review_ui.py`.
- 1 test i `breedings/test_leaderboard_columns.py` som låste en tidigare UI-ändring genom att kontrollera att texten `Placering` saknades i flera templates, utan att testa poäng- eller sorteringslogik.
- 1 test i `breedings/test_detail.py` som endast verifierade att listvyn innehöll länken till detaljsidan. Testerna för att ägaren får se detaljen och att andra användare nekas behålls.

### Test av implementation i stället för beteende

- 3 tester i `progression/test_background_color_picker.py`. Två av dem läste JavaScript-filen som text och sökte efter exakta kodsträngar för event handlers, maskning och färgsynkning; det tredje verifierade huvudsakligen att scriptet och fältet renderades. De testerna verifierar inte att JavaScript faktiskt fungerar i en webbläsare och blir lätt felaktigt röda vid ofarlig refaktorering.

## Tester som uttryckligen behålls

Vi behåller tester för:

- autentisering, behörighet, användarisolering och andra säkerhetsgränser,
- skapande, redigering och inskickning av odlingsrapporter,
- server-side-validering och dataintegritet,
- scoring, tävlingsregler och årsregler,
- progression, kravberäkning och konfigurerbara kravtexter,
- art-/taxonomilogik och omklassificering,
- URL- och redirectflöden där destinationen är en funktionell del av användarflödet,
- bildvalidering och server-side-regler för utmärkelsebilder och färgning.

## Medveten avvägning

Vi accepterar att vissa rena visuella regressioner inte längre fångas av Django-testsviten, till exempel ett ändrat Bootstrap-klassnamn, en extra rubrik, ändrad adminmenyordning, att en borttagen presentationskolumn återkommer eller att modalens exakta HTML ändras. Sådant bör i första hand upptäckas vid UI-granskning och tillgänglighetsarbete i stället för genom många backend-renderingstester som är dyra att underhålla.

Däremot har tester som skyddar behörighet, dataintegritet, domänregler eller centrala arbetsflöden inte tagits bort bara för att minska antalet tester.

## Resultat

Ingen produktionskod ändras i TEST-007. Körtid före och efter har inte kunnat mätas i GitHub-verktygsmiljön, så effekten dokumenteras som 20 färre testfall snarare än som en uppskattad tidsvinst. Hela testsviten ska köras lokalt innan merge.

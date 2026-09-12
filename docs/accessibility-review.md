# Tillgänglighetsgranskning – publika sidor och odlarläge

Granskningen hör till #259 och utgår från WCAG 2.2 nivå AA. Den är genomförd som en kod- och markupgranskning av den nuvarande Django/Bootstrap-implementationen på `main`. Den omfattar publika sidor, huvudnavigation, konto-/inloggningsflöden, odlingsregistrering, Min sida, topplistor, artinformation och gemensamma statusmeddelanden.

## Sammanfattning

Grundstrukturen är i flera avseenden bra: sidan har korrekt `lang="sv"`, en hoppa-till-innehåll-länk, semantiskt `main`, en namngiven huvudnavigation, en Bootstrap-menyknapp med `aria-controls`/`aria-expanded`, tydlig global `:focus-visible`, stöd för `prefers-reduced-motion`, textbaserade primära actions samt dekorativa logotyper som döljs för hjälpmedel.

De viktigaste kvarvarande riskerna ligger i tabellsemantik, formulärens hjälp-/feltexter och den mobila klickbara tabellraden. Därutöver finns mindre förbättringar i navigation, statusmeddelanden och ikon-/symbolhantering. Kontrast och faktisk upplevelse med skärmläsare/zoom behöver verifieras manuellt i körande miljö.

## Identifierade avvikelser och uppföljning

| Prioritet | Område | Observation | WCAG 2.2 | Rekommenderad åtgärd | Ärende |
| --- | --- | --- | --- | --- | --- |
| Hög | Tabeller | Flera publika tabeller använder kolumnrubriker utan explicit `scope` och saknar konsekvent tillgängligt namn/caption. Detta blir särskilt viktigt när kolumner döljs responsivt. | 1.3.1 Info and Relationships | Lägg till konsekvent tabellsemantik, `scope` och vid behov caption/tillgängligt namn. | #290 |
| Hög | Min sida, mobil | Den responsiva tabellraden får `role="link"` på `<tr>`. Det ersätter radens tabellroll och riskerar att bryta tabellstrukturen för skärmläsare. | 1.3.1 Info and Relationships, 4.1.2 Name, Role, Value | Behåll `<tr>` som rad och ge en verklig länk tydligt fokus-/hjälpmedelsstöd samtidigt som hela raden fortsatt kan tappas/klickas. | #292 |
| Hög | Formulär | Odlingsformuläret renderar hjälptexter manuellt utan id, medan widgets kan behöva `aria-describedby` till en stabil hjälptext-id. Felmeddelanden och felsammanfattning hanteras inte konsekvent mellan manuellt renderade formulär och `form.as_p`. | 1.3.1 Info and Relationships, 3.3.1 Error Identification, 3.3.2 Labels or Instructions, 4.1.3 Status Messages | Standardisera koppling mellan fält, hjälptext och fel; lägg till tydlig felsammanfattning där det behövs. | #291 |
| Medel | Huvudnavigation | Navigationen är namngiven och menyknappen korrekt uppmärkt, men aktuell huvudsektion markeras inte med `aria-current="page"`. | 1.3.1 Info and Relationships, 2.4.8 Location (AAA som vägledning) | Markera aktuell navigationslänk programmässigt och visuellt utan att enbart använda färg. | #293 |
| Medel | Statusmeddelanden | Globala Django-meddelanden använder `role="alert"`, men stängknappen har engelsk `aria-label="Close"` i en svensk tjänst. Informations-/varningsmeddelanden använder delvis annan semantik. | 3.1.2 Language of Parts, 4.1.3 Status Messages | Gör tillgängliga namn svenskspråkiga och standardisera semantik för status/alert/note. | #294 |
| Medel | Ikoner/symboler | Min sida använder exempelvis emoji för granskningskommentar. Den aktuella symbolen har `aria-label`, men mönstret behöver verifieras konsekvent för symboler, badges, ikonknappar och dekorativa bilder. | 1.1.1 Non-text Content, 4.1.2 Name, Role, Value | Gå igenom funktionella och dekorativa symboler och undvik både saknade namn och dubbel uppläsning. | #296 |
| Medel | Kontrast/fokus | SARF-paletten har tydliga fokusregler och textfärger i CSS, men statisk kodgranskning räcker inte för att verifiera alla faktiska kombinationer, Bootstrap-states, badges och fokusmarkeringar mot WCAG AA. | 1.4.3 Contrast (Minimum), 1.4.11 Non-text Contrast, 2.4.7 Focus Visible, 2.4.11 Focus Not Obscured (Minimum) | Mät faktiska färgkombinationer och verifiera fokus på relevanta bakgrunder. | #297 |

## Positiva observationer

- `templates/base.html` har svensk språkattribut, viewport och en skip-link till `#main-content`.
- `templates/includes/navigation.html` använder `<nav aria-label="Huvudnavigation">`; hamburgerknappen har tydligt tillgängligt namn, `aria-controls` och `aria-expanded` som Bootstrap uppdaterar.
- Headerlogotypen är dekorativ (`alt=""` och `aria-hidden="true"`) eftersom varumärkets namn redan finns i text intill.
- `static/css/site.css` har en global `:focus-visible`-indikering med outline och offset.
- Reducerad rörelse respekteras via `@media (prefers-reduced-motion: reduce)`.
- Vanliga kontoformulär använder Djangos standardrendering, vilket ger labels och grundläggande felmarkup utan egen JS.
- Centrala actions är riktiga länkar eller knappar i stället för klickbara generiska element.
- Modala utmärkelsevyer använder Bootstrap-modalens etablerade tangentbords- och fokusmodell.

## Områden utan konstaterad kodavvikelse men som behöver manuell verifiering

Följande går inte att avgöra tillräckligt säkert genom statisk kodgranskning och ligger därför i #295:

- faktisk tangentbordsordning genom alla centrala flöden,
- skärmläsarens uppläsning av modaler, dynamiska statusmeddelanden och valideringsfel,
- 200 % och 400 % zoom/reflow,
- fokus som kan döljas av sticky header eller modaler,
- touch-target-storlek i verkligt renderad layout,
- färgkontrast för samtliga Bootstrap-states och kombinationer,
- beteende när JavaScript är aktivt respektive när dynamiska delar uppdateras.

## Prioritering

1. #291 och #292 bör göras först eftersom de berör grundläggande relationer/roller i formulär och tabeller.
2. #290 bör göras i samma våg eftersom tabeller förekommer på flera centrala sidor.
3. #293, #294 och #296 är mindre men konkreta förbättringar med låg funktionell risk.
4. #297 och #295 bör avsluta granskningen genom mätning och manuell hjälpmedelstestning i körande miljö.

Denna PR ändrar ingen produktionskod. Alla implementationer är avsiktligt uppdelade i separata ärenden så att de kan genomföras och testas isolerat.
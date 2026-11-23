# Individuell topplista

Den individuella topplistan visar tävlingspoäng per kalenderår.

- Kalenderåret bestäms av odlingsregistreringens odlingsdatum.
- Endast godkända odlingsregistreringar räknas.
- Poängen beräknas med samma poänglogik som övrig tävlingspoäng i systemet.
- Publika resultat visar användarens publika användarnamn och ska inte falla tillbaka till e-post eller annan privat profilinformation.

## Sparade och beräknade poäng

Rapportens detaljsida visar `awarded_points`, de poäng som sparades vid
godkännandet. Ett avslag eller en återställning av godkännandet nollställer
tilldelningen. När en tidigare ej bedömd art får en klass uppdateras berörda
godkända rapporter enligt klassningsregeln.

Utmärkelser och karriärpoäng räknar från rapportens tilldelade klass.
Tävlingspoäng för ett avslutat år använder också rapportens tilldelade klass.
För innevarande år räknas tävlingspoäng med artens aktuella klass.

Kör `python manage.py audit_awarded_points` för att räkna godkända rapporter
där lagrade poäng saknas eller skiljer sig från den tilldelade klassens
poängtabell. Kommandot ändrar inga rapporter. Äldre tilldelningar kan avvika
och behöver bedömas innan en eventuell korrigering.

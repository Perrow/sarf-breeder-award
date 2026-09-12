# TEST-007 – förenkling av testsviten

Den här genomgången är medvetet konservativ. Målet är att minska tester som främst låser HTML/CSS-presentation utan att ge motsvarande skydd för affärslogik, behörighet eller dataintegritet.

## Borttagna tester

Totalt tas 6 tester bort:

- 4 tester i `users/test_form_layout.py` som verifierade att en CSS-fil gick att hitta och att specifika Bootstrap-/CSS-klasser fanns i login-, registrerings- och lösenordsåterställningsvyer. De testar huvudsakligen implementationsdetaljer i presentationen och ger liten extra trygghet jämfört med de funktionella användarflödena.
- 1 test i `users/test_min_page.py` som verifierade exakt titel, H1, navigationstext och frånvaro av den äldre texten `Mina odlingar`. Navigationens centrala ordning testas redan separat, medan login-redirecterna på Min sida behålls.
- 1 test i `users/test_navigation.py` som endast verifierade att den anonyma login-länken hade Bootstrap-klasserna `btn` och `btn-primary`. Funktionella navigationstester och POST-baserad logout behålls.

## Tester som uttryckligen behålls

- login-redirect till Min sida och respekt för `next`,
- ordningen för inloggad huvudnavigation,
- att logout är en POST-action,
- konto- och registreringsvalidering,
- behörighets- och säkerhetstester,
- dataintegritet och domänlogik i övriga appar.

## Avgränsning

Ingen produktionskod ändras. Genomgången rör endast `users`-tester som inte överlappar de samtidigt aktiva feature-brancherna för arter, förenings-URL, odlingslistor eller utmärkelsebilder.

Körtid före/efter har inte kunnat mätas i GitHub-verktygsmiljön. Effekten är därför dokumenterad som 6 färre testfall snarare än en uppskattad tidsvinst. Hela testsviten ska köras lokalt innan merge.
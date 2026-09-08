# Utgående e-post

Odlingskampanjen använder Djangos centrala e-postbackend. Lösenordsåterställning och framtida systemmail ska därför inte innehålla leverantörsspecifik SMTP-kod.

## Lokal utveckling

Utan särskild konfiguration används Djangos console-backend. Mail skrivs då till terminalen där utvecklingsservern körs och ingen extern SMTP-server behövs.

## SMTP i produktion

Sätt följande miljövariabler i driftmiljön:

- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST` – SMTP-serverns värdnamn
- `EMAIL_PORT` – SMTP-port, standardvärde 587
- `EMAIL_USE_TLS` – `true`/`false`
- `EMAIL_USE_SSL` – `true`/`false`
- `EMAIL_HOST_USER` – SMTP-användarnamn
- `EMAIL_HOST_PASSWORD` – SMTP-lösenord
- `DEFAULT_FROM_EMAIL` – standardavsändare, exempelvis `Odlingskampanjen <noreply@example.org>`

SMTP-lösenord och andra hemligheter ska endast lagras i driftmiljön och får inte checkas in i repositoryt.

`EMAIL_USE_TLS` och `EMAIL_USE_SSL` ska konfigureras enligt den valda SMTP-tjänsten; normalt används inte båda samtidigt.

Eftersom applikationskoden använder Djangos mail-API kan transporten senare ersättas med en API-baserad Django-email-backend utan att lösenordsåterställningens views eller domänlogik behöver ändras.

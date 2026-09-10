# Behörigheter

Applikationen använder både Django-rättigheter och domänroller.

## Django Admin

En användare måste vara markerad som `is_staff` för att kunna logga in i Django Admin. Därefter används Djangos modellrättigheter för de vanliga adminfunktionerna där de inte ersatts av en särskild domänregel.

För `Association` och `Membership` fungerar rättigheterna `view`, `add`, `change` och `delete` som globala modellrättigheter. En staff-användare som tilldelas exempelvis `view_association` kan därför se föreningar även utan rollen Föreningsadministratör.

## Domänroller

Rollerna `Systemadministratör` och `Föreningsadministratör` behålls. De styr föreningsspecifik åtkomst och kan ge åtkomst utan att motsvarande Django-rättighet har tilldelats separat. En föreningsadministratör begränsas fortfarande till de föreningar som användaren administrerar.

Granskning av odlingsregistreringar och övriga specialflöden som bygger på föreningsansvar fortsätter att använda dessa domänregler. Django-rättigheter ska alltså inte tolkas som en ersättning för föreningsrollerna där åtkomsten behöver avgränsas till en viss förening.

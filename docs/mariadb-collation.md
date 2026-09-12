# MariaDB-collation

Databasen ska använda teckenuppsättningen `utf8mb4` och collationen
`uca1400_swedish_as_ci`. Den är anpassad för svensk sortering, är
skiftlägesokänslig (`ci`) och accentkänslig (`as`). Det innebär exempelvis att
`Malawi` och `malawi` jämförs som samma namn, medan `Aland` och `Åland` är två
olika namn.

UCA 14-collationerna kräver MariaDB 10.10.1 eller senare. En lokal databas kan
skapas reproducerbart med:

```sql
CREATE DATABASE breeder_awards
    CHARACTER SET utf8mb4
    COLLATE uca1400_swedish_as_ci;
```

Samma teckenuppsättning och collation ska anges när databasen skapas i drift.
Kontrollera inställningen med:

```sql
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'breeder_awards';
```

## Unika textvärden

Följande domänvärden ska vara unika utan hänsyn till skiftläge men med hänsyn
till accenter:

- användarens interna e-postbaserade användarnamn och publika användarnamn,
- släktnamn och artgruppsnamn,
- geografiska namn,
- artnamn inom ett släkte,
- vetenskapliga och svenska synonymer inom en art,
- utmärkelsenamn och nivånamn inom en utmärkelse,
- konfigurerade kravtyper.

De relevanta domänfälten anger `uca1400_swedish_as_ci` uttryckligen. Övriga
textfält ärver databasens standardcollation. `SpeciesLink.url` är ett medvetet
undantag och använder `utf8mb4_bin`, eftersom sökväg och frågesträng i en URL
kan vara skiftlägeskänsliga.

SQLite-collationerna finns kvar enbart för uttryckliga, isolerade
kompatibilitetstester. Normal lokal utveckling och den ordinarie testsviten
använder MariaDB. Kör `./mariadbtest` för den fullständiga verifieringen.

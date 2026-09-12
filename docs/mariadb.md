# Lokal MariaDB

Applikationen använder MariaDB som enda normal databasbackend. SQLite används
inte längre för lokal utveckling eller tester. MariaDB 10.10.1 eller senare
krävs för projektets UCA 14-collationer.

## Installera server och byggberoenden i Ubuntu/WSL

```bash
sudo apt update
sudo apt install mariadb-server python3-dev default-libmysqlclient-dev build-essential pkg-config
sudo systemctl enable --now mariadb
```

`default-libmysqlclient-dev`, `build-essential` och `pkg-config` behövs för att
installera Python-paketet `mysqlclient` på Linux. Installera därefter projektets
Python-beroenden i den aktiverade virtuella miljön:

```bash
python -m pip install -r requirements.txt
```

## Läs in tidszonsdata

Projektet använder `USE_TZ=True`. MariaDB-serverns tidszonstabeller måste därför
läsas in en gång per server för att Djangos tidszonskonverteringar ska fungera:

```bash
sudo mariadb-tzinfo-to-sql /usr/share/zoneinfo | sudo mariadb mysql
```

På installationer där verktyget har det äldre namnet används i stället:

```bash
sudo mysql_tzinfo_to_sql /usr/share/zoneinfo | sudo mariadb mysql
```

## Skapa databas och användare

Välj egna lösenord och checka inte in dem i Git. Öppna MariaDB-klienten:

```bash
sudo mariadb
```

Skapa utvecklingsdatabasen och användaren:

```sql
CREATE DATABASE breeder_awards
    CHARACTER SET utf8mb4
    COLLATE uca1400_swedish_as_ci;

CREATE USER 'breeder_awards'@'127.0.0.1'
    IDENTIFIED BY 'byt-till-ett-lokalt-losenord';

GRANT ALL PRIVILEGES ON breeder_awards.*
    TO 'breeder_awards'@'127.0.0.1';
GRANT ALL PRIVILEGES ON test_breeder_awards.*
    TO 'breeder_awards'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Databasanslutningen sätter dessutom `default_storage_engine=INNODB` för varje
session, så att tabeller som Django skapar använder InnoDB och därmed stöder
transaktioner och främmande nycklar.

## Miljövariabler

Samtliga anslutningsvärden är obligatoriska:

```bash
export MARIADB_DATABASE=breeder_awards
export MARIADB_USER=breeder_awards
export MARIADB_PASSWORD='byt-till-ett-lokalt-losenord'
export MARIADB_HOST=127.0.0.1
export MARIADB_PORT=3306
```

Variablerna måste finnas i miljön för webbservern och för kommandon som
`migrate`, `test`, `pulltest` och `run`. Lägg dem exempelvis i en lokal fil som
är ignorerad av Git och läs in den i skalet innan skripten körs. `.env` är redan
ignorerad, men applikationen läser inte automatiskt in filen.

## Initiera och verifiera

Skapa alla tabeller i den tomma databasen och kontrollera anslutningen:

```bash
python manage.py migrate
python manage.py check --database default
```

Starta därefter applikationen som vanligt:

```bash
./run
```

Kör hela testsviten mot den separata testdatabasen:

```bash
python manage.py test
```

Django skapar automatiskt `test_breeder_awards` med `utf8mb4` och
`uca1400_swedish_as_ci` under testkörningen och tar normalt bort den efteråt.
Behåll den mellan körningar med `--keepdb` om det behövs.

Databasens teckenuppsättning och collation kan kontrolleras enligt
[collationdokumentationen](mariadb-collation.md).

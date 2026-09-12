# MariaDB lokalt och på server

Applikationen använder MariaDB som enda normal databasbackend. SQLite används
inte längre för lokal utveckling eller tester. MariaDB 10.10.1 eller senare
krävs för projektets UCA 14-collationer. MariaDB 10.11 LTS rekommenderas.

## Kontrollera versionen först

```bash
mariadb --version
```

Ubuntu 22.04 installerar MariaDB 10.6 från sin vanliga paketkälla. Den versionen
saknar `uca1400_swedish_as_ci` och kan därför inte användas av projektet. Ubuntu
24.04 levererar MariaDB 10.11 och kan använda distributionens paket direkt.

### Ubuntu 24.04

```bash
sudo apt update
sudo apt install mariadb-server mariadb-client python3-dev \
    default-libmysqlclient-dev build-essential pkg-config
sudo systemctl enable --now mariadb
```

### Ubuntu 22.04 och WSL

Konfigurera MariaDB:s officiella paketkälla innan MariaDB installeras:

```bash
sudo apt update
sudo apt install curl apt-transport-https
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup \
    | sudo bash -s -- \
        --mariadb-server-version="mariadb-10.11" \
        --skip-maxscale
sudo apt update
sudo apt install mariadb-server mariadb-client python3-dev \
    default-libmysqlclient-dev build-essential pkg-config
sudo systemctl enable --now mariadb
```

Om MariaDB 10.6 redan var installerad ska relevanta databaser säkerhetskopieras
först. Uppgradera sedan paketen, starta servern och kör uppgraderingsverktyget i
den ordningen:

```bash
sudo systemctl stop mariadb
sudo apt install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo mariadb-upgrade
sudo systemctl restart mariadb
```

I WSL utan systemd används `sudo service mariadb start` och
`sudo service mariadb restart` i stället. Kontrollera därefter att rätt version
och collation finns:

```bash
mariadb --version
sudo mariadb -e "SHOW COLLATION LIKE 'uca1400_swedish_as_ci';"
```

## Installera Python-beroenden

`default-libmysqlclient-dev`, `build-essential` och `pkg-config` behövs för
Python-paketet `mysqlclient`, som tillhandahåller modulen `MySQLdb`.

Skapa och aktivera den virtuella miljön från projektkatalogen:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verifiera vid problem med drivrutinen:

```bash
python -c "import MySQLdb; print('mysqlclient fungerar')"
```

## Läs in tidszonsdata

Projektet använder `USE_TZ=True`. MariaDB-serverns tidszonstabeller måste läsas
in en gång per server:

```bash
sudo mariadb-tzinfo-to-sql /usr/share/zoneinfo | sudo mariadb mysql
```

På installationer där verktyget har det äldre namnet används:

```bash
sudo mysql_tzinfo_to_sql /usr/share/zoneinfo | sudo mariadb mysql
```

## Lokal databas och användare

Öppna MariaDB-klienten med `sudo mariadb` och kör följande. Använd samma lösenord
som senare anges i `.env`:

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

Den extra behörigheten behövs för att Django ska kunna skapa och ta bort
`test_breeder_awards` när testsviten körs. På produktionsservern ska
applikationsanvändaren endast få behörighet till produktionsdatabasen.

Databasanslutningen sätter `default_storage_engine=INNODB` för varje session.
Den aktiverar även `STRICT_TRANS_TABLES` och använder Djangos normala
isolationsnivå `read committed`.

## Lokal `.env`

Skapa `.env` i projektets rot. Filen är ignorerad av Git och får inte checkas in:

```dotenv
MARIADB_DATABASE=breeder_awards
MARIADB_USER=breeder_awards
MARIADB_PASSWORD=byt-till-ett-lokalt-losenord
MARIADB_HOST=127.0.0.1
MARIADB_PORT=3306
```

Applikationen läser inte `.env` automatiskt. Läs in den i varje nytt terminalfönster:

```bash
set -a
source .env
set +a
```

Startas webbservern i bakgrunden måste även den processen startas om efter att
miljövariablerna har ändrats.

## Initiera, köra och testa lokalt

```bash
python manage.py check --database default
python manage.py migrate
./run
```

Webbplatsen finns då på `http://127.0.0.1:8000/`. Kör hela testsviten i ett
annat terminalfönster där `.env` också har lästs in:

```bash
./mariadbtest
```

`mariadbtest` avbryter om anslutningen inte går till MariaDB. Kommandot kör
Djangos databaskontroller, kontrollerar att modeller och migrationer stämmer
överens och kör därefter hela testsviten. Django skapar testdatabasen från noll
genom att applicera hela migrationshistoriken och tar bort den efter körningen.
Använd därför inte `--keepdb` för denna verifiering.

Skriptet `./pulltest` hämtar aktuell kod, migrerar databasen och kör samma
MariaDB-verifiering. Även det kräver att den virtuella miljön är aktiverad och
`.env` inläst.

Databasens teckenuppsättning och collation kan kontrolleras enligt
[collationdokumentationen](mariadb-collation.md).

## Felsökning

- `No module named 'MySQLdb'`: aktivera `.venv` och installera
  `requirements.txt`; installera byggberoendena ovan om installationen misslyckas.
- `Unknown database 'breeder_awards'`: skapa databasen enligt SQL-kommandona ovan
  och kontrollera `MARIADB_DATABASE`.
- `Unknown collation 'uca1400_swedish_as_ci'`: MariaDB är äldre än 10.10.1.
- `Can't connect ... mysqld.sock`: starta MariaDB innan `mariadb-upgrade` eller
  Django-kommandot körs.
- `Access denied`: kontrollera användare, lösenord, värdnamnet `127.0.0.1` och
  resultatet från `SHOW GRANTS FOR 'breeder_awards'@'127.0.0.1';`.

För installation av hela applikationen i drift, se
[serverinstallationen](server-setup.md).

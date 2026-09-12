# Backup och återställning

Produktionsbackupen består av två separata objekt:

1. en logisk MariaDB-dump med databasens schema och data,
2. ett arkiv av uppladdade filer i `/var/www/breeder-awards/media`.

Källkoden, den virtuella Pythonmiljön och `staticfiles/` ingår inte. De skapas
på nytt från Git, `requirements.txt` och `collectstatic`. Det finns ingen
SQLite-fil att kopiera och ingen SQLite-till-MariaDB-konvertering ingår.

Backupfilerna innehåller personuppgifter och ska krypteras vid lagring och
överföring. De ska kopieras från applikationsservern till separat lagring med
versionshistorik. Bestäm och dokumentera ansvarig person, körfrekvens,
lagringstid och off-site-mål för den faktiska driftsmiljön. En backup är inte
godkänd förrän en återställning har provats.

Som miniminivå ska backup tas varje dygn och omedelbart före varje driftsättning
som kan ändra schema eller data. Kopiera varje lyckad uppsättning off-site
direkt. En lämplig startpunkt för retention är 14 dagliga, 8 veckovisa och 12
månadsvisa uppsättningar; justera detta när verksamheten har fastställt krav på
maximal dataförlust och återställningstid. Genomför restore-verifieringen minst
kvartalsvis och efter varje förändring av backup- eller återställningsrutinen.

## Förbered backupkontot

Backupkontot skapas med läsrättigheter enligt
[serverinstallationen](server-setup.md#2-skapa-produktionsdatabasen-och-konton-med-minsta-behörighet).
Lägg anslutningen i `/etc/mysql/breeder-awards-backup.cnf`:

```ini
[client]
host=127.0.0.1
user=breeder_awards_backup
password=byt-till-backup-losenordet
```

```bash
sudo chown root:root /etc/mysql/breeder-awards-backup.cnf
sudo chmod 600 /etc/mysql/breeder-awards-backup.cnf
sudo install -d -m 700 -o root -g root /var/backups/breeder-awards
```

Lösenordet ska inte anges på kommandoraden, eftersom det då kan synas i
processlistor och skalhistorik. `--defaults-extra-file` måste vara första
argumentet till MariaDB-klienten.

## Skapa en backup

Exemplet ger databasen och media samma tidsstämpel men lagrar dem i separata
filer. För en helt konsekvent uppsättning stoppas webbprocessen medan båda
objekten tas. MariaDB-servern ska fortsätta vara igång.

```bash
sudo -i
set -euo pipefail
umask 077
BACKUP_DIR=/var/backups/breeder-awards
BACKUP_STAMP=$(date -u +%Y%m%dT%H%M%SZ)

systemctl stop breeder-awards
trap 'systemctl start breeder-awards' EXIT

mariadb-dump \
  --defaults-extra-file=/etc/mysql/breeder-awards-backup.cnf \
  --single-transaction \
  --quick \
  --skip-lock-tables \
  --no-tablespaces \
  --default-character-set=utf8mb4 \
  breeder_awards \
  | gzip -9 > "$BACKUP_DIR/database-$BACKUP_STAMP.sql.gz"

tar -C /var/www/breeder-awards \
  -czf "$BACKUP_DIR/media-$BACKUP_STAMP.tar.gz" media

systemctl start breeder-awards
trap - EXIT

cd "$BACKUP_DIR"
sha256sum \
  "database-$BACKUP_STAMP.sql.gz" \
  "media-$BACKUP_STAMP.tar.gz" \
  > "backup-$BACKUP_STAMP.sha256"
exit
```

Kontrollera att tjänsten åter är igång även om ett backupkommando misslyckas:

```bash
sudo systemctl status breeder-awards --no-pager
```

Kopiera de två backupfilerna och checksummefilen tillsammans till den separata
backuplagringen. En lokal fil i `/var/backups` är endast en mellanlagring och
skyddar inte mot diskfel eller förlust av servern.

## Kontrollera backupfilerna

```bash
sudo -i
cd /var/backups/breeder-awards
sha256sum --check backup-YYYYMMDDTHHMMSSZ.sha256
gzip --test database-YYYYMMDDTHHMMSSZ.sql.gz
tar -tzf media-YYYYMMDDTHHMMSSZ.tar.gz >/dev/null
exit
```

Kontrollen visar att filerna kan läsas och inte har ändrats. Den ersätter inte
restore-verifieringen nedan.

## Verifiera restore utan att påverka produktion

Gör detta regelbundet och efter ändringar i backupförfarandet. Använd en tom,
tillfällig databas och en separat användare; återställ aldrig ett test ovanpå
produktionsdatabasen.

Öppna `sudo mariadb` och kör:

```sql
CREATE DATABASE breeder_awards_restore_verify
    CHARACTER SET utf8mb4
    COLLATE uca1400_swedish_as_ci;

CREATE USER 'breeder_awards_restore_verify'@'127.0.0.1'
    IDENTIFIED BY 'byt-till-ett-tillfalligt-losenord';

GRANT SELECT ON breeder_awards_restore_verify.*
    TO 'breeder_awards_restore_verify'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Skapa `/etc/breeder-awards-restore-verify.env` med samma tillfälliga uppgifter:

```dotenv
MARIADB_DATABASE=breeder_awards_restore_verify
MARIADB_USER=breeder_awards_restore_verify
MARIADB_PASSWORD=byt-till-ett-tillfalligt-losenord
MARIADB_HOST=127.0.0.1
MARIADB_PORT=3306
```

```bash
sudo chown root:breeder-awards /etc/breeder-awards-restore-verify.env
sudo chmod 640 /etc/breeder-awards-restore-verify.env
```

Återställ dumpen som databasadministratör:

```bash
sudo bash -o pipefail -c '
  gzip -cd /var/backups/breeder-awards/database-YYYYMMDDTHHMMSSZ.sql.gz \
    | mariadb breeder_awards_restore_verify
'
```

Verifiera med Django utan att ändra `/etc/breeder-awards.env`:

```bash
sudo -u breeder-awards bash -c '
  set -a
  source /etc/breeder-awards-restore-verify.env
  set +a
  cd /var/www/breeder-awards
  .venv/bin/python manage.py check --database default
  .venv/bin/python manage.py migrate --check
  .venv/bin/python manage.py shell --command \
    "from users.models import User; print(f'Återställda användare: {User.objects.count()}')"
'
```

Verifiera mediaarkivet separat i en tom temporär katalog:

```bash
RESTORE_MEDIA_DIR=$(mktemp -d)
sudo tar -xzf /var/backups/breeder-awards/media-YYYYMMDDTHHMMSSZ.tar.gz \
  -C "$RESTORE_MEDIA_DIR"
find "$RESTORE_MEDIA_DIR/media" -type f | head
```

När verifieringen är dokumenterad och godkänd kan testobjekten tas bort:

```sql
DROP DATABASE breeder_awards_restore_verify;
DROP USER 'breeder_awards_restore_verify'@'127.0.0.1';
```

Radera även `/etc/breeder-awards-restore-verify.env` och den temporära
mediakatalogen.

## Återställ produktionen

1. Stoppa `breeder-awards` så att inga nya skrivningar sker.
2. Kontrollera checksummorna och ta en separat säkerhetskopia av nuvarande
   databas och media innan något byts ut.
3. Skapa en ny tom databas med `utf8mb4` och
   `uca1400_swedish_as_ci`; återställ dumpen till den nya databasen i stället
   för att skriva över den befintliga.
4. Kör Django-verifieringen ovan mot den återställda databasen.
5. Packa upp mediaarkivet till en ny katalog. Flytta den befintliga
   `media/`-katalogen till ett tidsstämplat reservnamn och flytta därefter den
   återställda katalogen till `/var/www/breeder-awards/media`.
6. Ge `breeder_awards_app`, `breeder_awards_deploy` och
   `breeder_awards_backup` samma respektive rättigheter till den återställda
   databasen som i serverinstallationen. Ändra `MARIADB_DATABASE` i
   `/etc/breeder-awards.env` till det nya databasnamnet och använd samma namn i
   det schemalagda dumpkommandot.
7. Starta tjänsten och kontrollera webbplatsen samt
   `journalctl -u breeder-awards`.
8. Behåll den tidigare databasen och mediakatalogen tills återställningen har
   verifierats och godkänts. Återgång görs genom att återställa föregående
   databasnamn och mediakatalog.

## Verifiera driftförutsättningarna

Kör efter installation, återställning och större MariaDB-uppgraderingar:

```bash
sudo -u breeder-awards bash -c '
  set -a
  source /etc/breeder-awards.env
  set +a
  cd /var/www/breeder-awards
  .venv/bin/python manage.py check --database default
  .venv/bin/python manage.py shell --command \
    "from django.db import connection; print(connection.mysql_version, connection.sql_mode, connection.isolation_level)"
'

sudo mariadb -e "
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME='breeder_awards';
SELECT TABLE_NAME, ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA='breeder_awards' AND ENGINE <> 'InnoDB';"
```

Förväntat resultat är MariaDB 10.10.1 eller senare, `utf8mb4`, collation
`utf8mb4_uca1400_swedish_as_ci`, strict mode (`STRICT_TRANS_TABLES` eller
striktare), `read committed` och inga applikationstabeller med annan motor än
InnoDB.

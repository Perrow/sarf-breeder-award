# Serverinstallation

Den här guiden beskriver en enkel installation på en Ubuntu 24.04-server där
Nginx terminerar HTTPS och skickar anrop till Gunicorn/Django. MariaDB körs på
samma server. Anpassa domännamn, lösenord och sökvägar till driftmiljön.

## 1. Installera systempaket

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-dev nginx certbot \
    python3-certbot-nginx mariadb-server mariadb-client \
    default-libmysqlclient-dev build-essential pkg-config
sudo systemctl enable --now mariadb nginx
```

Ubuntu 24.04 innehåller MariaDB 10.11. Kontrollera att versionen och projektets
collation finns:

```bash
mariadb --version
sudo mariadb -e "SHOW COLLATION LIKE 'uca1400_swedish_as_ci';"
```

Används Ubuntu 22.04 måste MariaDB:s officiella 10.11-paketkälla först läggas
till enligt [MariaDB-guiden](mariadb.md#ubuntu-2204-och-wsl).

Läs därefter in systemets tidszoner:

```bash
sudo mariadb-tzinfo-to-sql /usr/share/zoneinfo | sudo mariadb mysql
```

## 2. Skapa produktionsdatabasen och konton med minsta behörighet

Använd separata konton för normal drift, migreringar och backup. Då kan
webbprocessen inte ändra databasens schema och backupkontot kan inte skriva data.
Öppna `sudo mariadb` och välj tre unika, långa lösenord:

```sql
CREATE DATABASE breeder_awards
    CHARACTER SET utf8mb4
    COLLATE uca1400_swedish_as_ci;

CREATE USER 'breeder_awards_app'@'127.0.0.1'
    IDENTIFIED BY 'byt-till-appens-losenord';
CREATE USER 'breeder_awards_deploy'@'127.0.0.1'
    IDENTIFIED BY 'byt-till-deploy-losenordet';
CREATE USER 'breeder_awards_backup'@'127.0.0.1'
    IDENTIFIED BY 'byt-till-backup-losenordet';

GRANT SELECT, INSERT, UPDATE, DELETE ON breeder_awards.*
    TO 'breeder_awards_app'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, REFERENCES
    ON breeder_awards.* TO 'breeder_awards_deploy'@'127.0.0.1';

GRANT SELECT, SHOW VIEW, TRIGGER ON breeder_awards.*
    TO 'breeder_awards_backup'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Kontrollera rättigheterna med `SHOW GRANTS FOR
'breeder_awards_app'@'127.0.0.1';` och motsvarande kommando för de andra två
kontona. Inget produktionskonto får behörighet till `test_breeder_awards`. Kör
inte testsviten med produktionsmiljön eller produktionskontona.

## 3. Installera applikationen

Skapa ett separat systemkonto och hämta koden:

```bash
sudo useradd --system --create-home --home-dir /var/lib/breeder-awards \
    --shell /usr/sbin/nologin breeder-awards
sudo mkdir -p /var/www/breeder-awards
sudo chown breeder-awards:breeder-awards /var/www/breeder-awards
sudo -u breeder-awards git clone \
    https://github.com/Perrow/sarf-breeder-award.git \
    /var/www/breeder-awards
```

Skapa den virtuella miljön och installera beroendena:

```bash
sudo -u breeder-awards python3 -m venv /var/www/breeder-awards/.venv
sudo -u breeder-awards /var/www/breeder-awards/.venv/bin/python \
    -m pip install --upgrade pip
sudo -u breeder-awards /var/www/breeder-awards/.venv/bin/python \
    -m pip install -r /var/www/breeder-awards/requirements.txt
```

## 4. Konfigurera produktionsmiljön

Generera en Django-nyckel:

```bash
/var/www/breeder-awards/.venv/bin/python -c \
    "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Skapa `/etc/breeder-awards.env` som root. Ange inte `export` i filen:

```dotenv
DJANGO_ENV=production
DJANGO_SECRET_KEY=byt-till-den-genererade-nyckeln
DJANGO_ALLOWED_HOSTS=example.org,www.example.org
MARIADB_DATABASE=breeder_awards
MARIADB_USER=breeder_awards_app
MARIADB_PASSWORD=byt-till-appens-losenord
MARIADB_HOST=127.0.0.1
MARIADB_PORT=3306
```

SMTP-inställningarna beskrivs i [e-postguiden](email.md). Skydda filen men låt
tjänstekontot läsa den:

```bash
sudo chown root:breeder-awards /etc/breeder-awards.env
sudo chmod 640 /etc/breeder-awards.env
```

Skapa även `/etc/breeder-awards-deploy.env`, endast läsbar för root:

```dotenv
MARIADB_USER=breeder_awards_deploy
MARIADB_PASSWORD=byt-till-deploy-losenordet
```

```bash
sudo chown root:root /etc/breeder-awards-deploy.env
sudo chmod 600 /etc/breeder-awards-deploy.env
```

Kontrollera inställningarna, migrera och samla statiska filer:

```bash
sudo bash -c '
  set -a
  source /etc/breeder-awards.env
  source /etc/breeder-awards-deploy.env
  set +a
  cd /var/www/breeder-awards
  sudo -u breeder-awards --preserve-env \
    .venv/bin/python manage.py check --deploy
  sudo -u breeder-awards --preserve-env \
    .venv/bin/python manage.py migrate
  sudo -u breeder-awards --preserve-env \
    .venv/bin/python manage.py collectstatic --noinput
'
```

Kontrollera därefter driftförutsättningarna enligt
[backup- och återställningsguiden](backup-restore.md#verifiera-driftförutsättningarna).

## 5. Kör Django med systemd och Gunicorn

Skapa `/etc/systemd/system/breeder-awards.service`:

```ini
[Unit]
Description=Odlingskampanjen Gunicorn
After=network.target mariadb.service

[Service]
Type=simple
User=breeder-awards
Group=www-data
WorkingDirectory=/var/www/breeder-awards
EnvironmentFile=/etc/breeder-awards.env
RuntimeDirectory=breeder-awards
RuntimeDirectoryMode=0755
ExecStart=/var/www/breeder-awards/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/breeder-awards/gunicorn.sock \
    --umask 007 \
    breeder_awards.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktivera tjänsten:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now breeder-awards
sudo systemctl status breeder-awards --no-pager
```

Loggar visas med:

```bash
sudo journalctl -u breeder-awards -f
```

## 6. Konfigurera Nginx och HTTPS

Skapa `/etc/nginx/sites-available/breeder-awards` och byt domännamnen:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name example.org www.example.org;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/breeder-awards/staticfiles/;
    }

    location /media/ {
        alias /var/www/breeder-awards/media/;
    }

    location / {
        include proxy_params;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/breeder-awards/gunicorn.sock;
    }
}
```

Aktivera webbplatsen och kontrollera konfigurationen:

```bash
sudo ln -s /etc/nginx/sites-available/breeder-awards \
    /etc/nginx/sites-enabled/breeder-awards
sudo nginx -t
sudo systemctl reload nginx
```

När DNS pekar på servern hämtas och konfigureras certifikatet:

```bash
sudo certbot --nginx -d example.org -d www.example.org
sudo certbot renew --dry-run
```

Django litar i produktionsläge på `X-Forwarded-Proto` från proxyn. Nginx måste
därför sätta headern enligt konfigurationen ovan.

## 7. Uppdatera servern

Ta databas- och mediabackup enligt [backupguiden](backup-restore.md) före en
uppdatering. Uppdatera därefter från `main`:

```bash
sudo -u breeder-awards bash -c '
  cd /var/www/breeder-awards
  git pull --ff-only
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python manage.py collectstatic --noinput
'
sudo bash -c '
  set -a
  source /etc/breeder-awards.env
  source /etc/breeder-awards-deploy.env
  set +a
  cd /var/www/breeder-awards
  sudo -u breeder-awards --preserve-env \
    .venv/bin/python manage.py migrate
'
sudo systemctl restart breeder-awards
sudo systemctl status breeder-awards --no-pager
```

Kontrollera efteråt webbplatsen och tjänstens logg.

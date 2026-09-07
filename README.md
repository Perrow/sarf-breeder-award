# SARF Breeder Award

Breeder Award Program for multiple associations.

## BA-001 – Django project

The repository contains the initial Django project scaffold. It uses SQLite for local storage and the standard Django administration endpoint.

### Requirements

- Python 3.12 or newer

### Local setup

```bash
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies and initialize the database:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

The development site is then available at `http://127.0.0.1:8000/`. The `/admin/` route is provided by Django; no application-specific functionality is part of BA-001.

### Verification

Run Django's system checks:

```bash
python manage.py check
```

# SARF Breeder Award

Breeder Award Program for multiple associations.

## Requirements

- Python 3.12 or newer

## Local setup

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

The development site is then available at `http://127.0.0.1:8000/`. The Django administration site is available at `/admin/`.

## BA-001 – Django project

The repository contains the initial Django project scaffold using SQLite.

## BA-002 – Custom User model

The project uses its own `users.User` model, based on Django's `AbstractUser`. It is configured through `AUTH_USER_MODEL = "users.User"` and registered with the standard Django admin user interface.

BA-002 deliberately adds no application-specific user fields. Future tasks can extend the project-owned user model without replacing Django's built-in user model after database migrations have been established.

For a new local database, apply migrations with:

```bash
python manage.py migrate
```

### Verification

Run Django's system checks and confirm that no model changes are missing migrations:

```bash
python manage.py check
python manage.py makemigrations --check
```

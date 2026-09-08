# Odlingskampanjen

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

## SQ-001 – Swedish site

The application is named **Odlingskampanjen** and uses Swedish throughout, including Django's built-in administration interface and translated validation messages.

## BA-001 – Django project

The repository contains the initial Django project scaffold using SQLite.

## BA-002 – Custom User model

The project uses its own `users.User` model, based on Django's `AbstractUser`. It is configured through `AUTH_USER_MODEL = "users.User"` and registered with the standard Django admin user interface.

BA-002 deliberately adds no application-specific user fields. Future tasks can extend the project-owned user model without replacing Django's built-in user model after database migrations have been established.

## BA-003 – Basic templates and Bootstrap

The project has a shared Django template structure with `templates/base.html`, a home page and reusable navigation, messages and footer includes. Bootstrap 5 is loaded by the base template, and the navigation collapses on smaller screens.

Application templates inherit `base.html`. Django messages are rendered through the shared messages include.

## BA-010 – User accounts

Visitors can create an account with name, email address and password at `/accounts/register/`. The email address is used as the account's internal Django username, so users do not need a separate username.

Registered users can log in with email and password at `/accounts/login/` and log out from their account page. `/account/` is login-protected and redirects anonymous visitors to the login page.

Run the BA-010 account tests with:

```bash
python manage.py test users
```

## BA-011 – Associations and memberships

The `associations` app contains the `Association` and `Membership` models. Associations store their name, organization number, contact details, address and description. A membership links one user to one association and can store a member number and association-specific information.

A user can belong to multiple associations. The same user cannot have duplicate memberships in the same association.

Apply the BA-011 migration with:

```bash
python manage.py migrate
```

Run the BA-011 model tests with:

```bash
python manage.py test associations
```

## BA-020 – Genera

Scientific genera are stored separately in `taxonomy.Genus`. A genus has a required unique scientific name and an active/inactive flag. Inactivation preserves the genus record so it can remain referenced by historical data.

Apply the BA-020 migration with:

```bash
python manage.py migrate
```

Run the genus model tests with:

```bash
python manage.py test taxonomy
```

### Verification

Run Django's system checks and the test suite:

```bash
python manage.py check
python manage.py test
```

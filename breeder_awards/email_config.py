import os


def _env_bool(environ, name, default=False):
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_email_settings(environ=None):
    environ = os.environ if environ is None else environ
    return {
        "EMAIL_BACKEND": environ.get(
            "EMAIL_BACKEND",
            "django.core.mail.backends.console.EmailBackend",
        ),
        "EMAIL_HOST": environ.get("EMAIL_HOST", ""),
        "EMAIL_PORT": int(environ.get("EMAIL_PORT", "587")),
        "EMAIL_USE_TLS": _env_bool(environ, "EMAIL_USE_TLS", False),
        "EMAIL_USE_SSL": _env_bool(environ, "EMAIL_USE_SSL", False),
        "EMAIL_HOST_USER": environ.get("EMAIL_HOST_USER", ""),
        "EMAIL_HOST_PASSWORD": environ.get("EMAIL_HOST_PASSWORD", ""),
        "DEFAULT_FROM_EMAIL": environ.get(
            "DEFAULT_FROM_EMAIL",
            "Odlingskampanjen <noreply@localhost>",
        ),
    }

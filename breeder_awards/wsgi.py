"""WSGI config for the Breeder Awards project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breeder_awards.settings")

application = get_wsgi_application()

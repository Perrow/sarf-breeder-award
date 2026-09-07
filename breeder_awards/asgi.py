"""ASGI config for the Breeder Awards project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breeder_awards.settings")

application = get_asgi_application()

from .settings import *  # noqa


DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "dev.db"}}
ALLOWED_HOSTS = ("localhost",)

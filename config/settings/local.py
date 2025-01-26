# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="VT4PkfZUaNHAL1exa2qpB6qKotonXNBQR3gdhYLtai5oZt2efGsVqmRiUgNqR04s",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]  # noqa: S104

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
USE_THIRD_PARTY_EMAIL_SERVICE = env("USE_THIRD_PARTY_EMAIL_SERVICE", default=False)

if USE_THIRD_PARTY_EMAIL_SERVICE:
    DOMAIN_NAME = env("DJANGO_DOMAIN_NAME", default="")
    DEFAULT_FROM_EMAIL = env(
        "DJANGO_DEFAULT_FROM_EMAIL",
        default=f"ATG <noreply@{DOMAIN_NAME}>",
    )
    # https://docs.djangoproject.com/en/dev/ref/settings/#server-email
    SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
    EMAIL_SUBJECT_PREFIX = env(
        "DJANGO_EMAIL_SUBJECT_PREFIX",
        default="[ATG] ",
    )
    ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX

    # Anymail
    # ------------------------------------------------------------------------------
    # https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
    INSTALLED_APPS += ["anymail"]
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
    # https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
    # https://anymail.readthedocs.io/en/stable/esps/mailjet/
    EMAIL_BACKEND = "anymail.backends.mailjet.EmailBackend"
    ANYMAIL = {
        "MAILJET_API_KEY": env("MAILJET_API_KEY"),
        "MAILJET_SECRET_KEY": env("MAILJET_SECRET_KEY"),
    }
else:
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-host
    EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-port
    EMAIL_PORT = 1025

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
]  # Add your frontend URL here.
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Disable profiling panel due to an issue with Python 3.12:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
    # RunServerPlus
    # ------------------------------------------------------------------------------
    # This is a custom setting for RunServerPlus to fix reloader issue in Windows docker environment
    # Werkzeug reloader type [auto, watchdog, or stat]
    RUNSERVERPLUS_POLLER_RELOADER_TYPE = "stat"
    # If you have CPU and IO load issues, you can increase this poller interval e.g) 5
    RUNSERVERPLUS_POLLER_RELOADER_INTERVAL = 1

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]
# Celery
# ------------------------------------------------------------------------------

# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True
# Vue
# -------------------------------------------------------------------------------
VUE_FRONTEND_USE_DEV_SERVER = True

# Add artificial delay to API responses (in seconds)
DEBUG_API_DELAY = 0
DEBUG_API_ENDPOINTS_TO_DELAY = ["/api/requests"]
MIDDLEWARE += ["config.delay_middleware.DelayMiddleware"]

# Add artificial delay to shared tasks (in seconds)
TASK_DELAY = 0

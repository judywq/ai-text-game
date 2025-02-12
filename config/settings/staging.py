from .base import MIDDLEWARE
from .base import env
from .production import *  # noqa: F403

# SECURITY
# ------------------------------------------------------------------------------
# Use the default cookie settings if not using HTTPS
USE_HTTPS = env.bool("DJANGO_USE_HTTPS", default=False)
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
if not USE_HTTPS:
    SESSION_COOKIE_NAME = "sessionid"
    CSRF_COOKIE_NAME = "csrftoken"

MIDDLEWARE = [
    "config.middleware.RequestLoggingMiddleware",
    *MIDDLEWARE,
]

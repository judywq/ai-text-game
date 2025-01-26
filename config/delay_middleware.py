import logging
import time

from django.conf import settings

logger = logging.getLogger(__name__)


class DelayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        delay = getattr(settings, "DEBUG_API_DELAY", 0)
        if delay > 0:
            endpoints_to_delay = getattr(settings, "DEBUG_API_ENDPOINTS_TO_DELAY", [])
            if endpoints_to_delay:
                for endpoint in endpoints_to_delay:
                    if request.path.startswith(endpoint):
                        msg = f"Delaying API request by {delay} seconds"
                        logger.info(msg)
                        time.sleep(delay)
                        break

        return self.get_response(request)

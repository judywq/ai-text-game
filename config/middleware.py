import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug(
            "--------------> Incoming request: %s %s",
            request.method,
            request.path,
        )
        logger.debug(
            "--------------> Headers: %s",
            dict(request.headers),
        )
        response = self.get_response(request)
        logger.debug("--------------> Response status: %s", response.status_code)
        return response

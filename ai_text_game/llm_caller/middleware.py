from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Get query string from scope
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        # Get token from query params
        token_key = query_params.get("token", [None])[0]

        if token_key:
            # Get user from token
            try:
                user = await self.get_user_from_token(token_key)
                scope["user"] = user
            except Token.DoesNotExist:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        token = Token.objects.select_related("user").get(key=token_key)
        return token.user

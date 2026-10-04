"""
JWT auth for WebSocket connections. Token is passed as query param: ?token=<access_token>
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def get_user_from_scope(scope):
    """Extract and validate JWT from query string; return user or AnonymousUser."""
    query_string = scope.get('query_string', b'')
    if isinstance(query_string, bytes):
        query_string = query_string.decode('utf-8')
    params = parse_qs(query_string)
    tokens = params.get('token', [])
    if not tokens:
        return AnonymousUser()
    token_str = tokens[0]
    try:
        access = AccessToken(token_str)
        user_id = access.get('user_id')
    except (TokenError, InvalidToken, KeyError, TypeError):
        return AnonymousUser()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware:
    """Add scope['user'] from JWT in query string."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            from asgiref.sync import sync_to_async
            scope['user'] = await sync_to_async(get_user_from_scope)(scope)
        await self.app(scope, receive, send)





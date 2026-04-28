from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.models import User, UserSession


@database_sync_to_async
def get_user_from_token(token_string, session_id=None):
    try:
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        
        if session_id:
            try:
                session = UserSession.objects.get(
                    session_id=session_id,
                    user=user,
                    is_active=True
                )
                return user, session
            except UserSession.DoesNotExist:
                return AnonymousUser(), None
        
        token_session_id = access_token.get('session_id')
        if token_session_id:
            try:
                session = UserSession.objects.get(
                    session_id=token_session_id,
                    user=user,
                    is_active=True
                )
                return user, session
            except UserSession.DoesNotExist:
                return AnonymousUser(), None
        
        return user, None
        
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser(), None


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        session_id = query_params.get('session_id', [None])[0]

        if token:
            user, session = await get_user_from_token(token, session_id)
            scope['user'] = user
            scope['session'] = session
        else:
            scope['user'] = AnonymousUser()
            scope['session'] = None

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)

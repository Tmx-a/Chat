import uuid
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions
from .models import UserSession


class SessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        
        user, validated_token = result
        
        session_id = request.META.get('HTTP_X_SESSION_ID')
        if not session_id:
            try:
                session_id = validated_token.get('session_id')
            except Exception:
                pass
        
        if session_id:
            try:
                session = UserSession.objects.get(
                    session_id=session_id,
                    user=user,
                    is_active=True
                )
                request.session_obj = session
            except UserSession.DoesNotExist:
                raise exceptions.AuthenticationFailed('会话已失效，请重新登录')
        
        return (user, validated_token)

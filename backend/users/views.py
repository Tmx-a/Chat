from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, UserSession
from .serializers import UserSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': '注册成功'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
            user.save()
            return Response(UserSerializer(user).data)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id)


class OnlineUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)
        serializer = UserSerializer(online_users, many=True)
        return Response(serializer.data)


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
        users = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id)[:10]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not old_password or not new_password:
            return Response({'error': '请填写完整信息'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            return Response({'error': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'error': '新密码至少6位'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': '密码修改成功'})


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'message': '账号已注销'})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        
        if not username or not password:
            return Response({'error': '请输入用户名和密码'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        device_name = UserSession.get_device_name(user_agent)
        
        session = UserSession.objects.create(
            user=user,
            device_info=user_agent[:256],
            device_name=device_name,
            ip_address=ip_address,
            refresh_token=str(refresh)
        )
        
        refresh['session_id'] = str(session.session_id)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'session_id': str(session.session_id),
            'user': UserSerializer(user).data,
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class UserSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        )
        current_session_id = request.META.get('HTTP_X_SESSION_ID')
        
        data = []
        for session in sessions:
            data.append({
                'id': str(session.session_id),
                'device_name': session.device_name,
                'device_info': session.device_info[:50] + '...' if len(session.device_info) > 50 else session.device_info,
                'ip_address': session.ip_address,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_current': str(session.session_id) == current_session_id,
            })
        return Response(data)


class KickSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        try:
            session = UserSession.objects.get(
                session_id=session_id,
                user=request.user
            )
        except UserSession.DoesNotExist:
            return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        current_session_id = request.META.get('HTTP_X_SESSION_ID')
        if str(session.session_id) == current_session_id:
            return Response({'error': '不能踢出当前设备'}, status=status.HTTP_400_BAD_REQUEST)
        
        session.is_active = False
        session.save()
        return Response({'message': '已踢出该设备'})


class LogoutAllOtherView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_session_id = request.META.get('HTTP_X_SESSION_ID')
        
        updated = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(
            session_id=current_session_id
        ).update(is_active=False)
        
        return Response({'message': f'已踢出 {updated} 个其他设备'})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_session_id = request.META.get('HTTP_X_SESSION_ID')
        
        if current_session_id:
            UserSession.objects.filter(
                session_id=current_session_id,
                user=request.user
            ).update(is_active=False)
        
        return Response({'message': '已退出登录'})

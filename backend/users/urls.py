from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, UserProfileView, UserListView, OnlineUsersView,
    UserSearchView, ChangePasswordView, DeleteAccountView,
    LoginView, UserSessionListView, KickSessionView, LogoutAllOtherView, LogoutView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('list/', UserListView.as_view(), name='user_list'),
    path('online/', OnlineUsersView.as_view(), name='online_users'),
    path('search/', UserSearchView.as_view(), name='user_search'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('account/', DeleteAccountView.as_view(), name='delete_account'),
    path('sessions/', UserSessionListView.as_view(), name='user_sessions'),
    path('sessions/<str:session_id>/kick/', KickSessionView.as_view(), name='kick_session'),
    path('sessions/logout-all/', LogoutAllOtherView.as_view(), name='logout_all_other'),
]

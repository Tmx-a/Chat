import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ONLINE = 'online'
    BUSY = 'busy'
    AWAY = 'away'
    INVISIBLE = 'invisible'
    STATUS_CHOICES = [
        (ONLINE, 'Online'),
        (BUSY, 'Busy'),
        (AWAY, 'Away'),
        (INVISIBLE, 'Invisible'),
    ]
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, default='')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    signature = models.CharField(max_length=256, blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ONLINE)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    refresh_token = models.CharField(max_length=512, blank=True, default='')
    device_info = models.CharField(max_length=256, blank=True, default='')
    device_name = models.CharField(max_length=64, blank=True, default='')
    ip_address = models.CharField(max_length=45, blank=True, default='')
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.device_name or self.device_info[:30]}'

    @staticmethod
    def get_device_name(user_agent):
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            if 'iphone' in ua_lower:
                return 'iPhone'
            elif 'android' in ua_lower:
                return 'Android'
            return '移动设备'
        elif 'windows' in ua_lower:
            return 'Windows PC'
        elif 'mac' in ua_lower:
            return 'Mac'
        elif 'linux' in ua_lower:
            return 'Linux'
        return '未知设备'

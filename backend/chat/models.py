from django.db import models
from users.models import User
import uuid


class FriendGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_groups')
    name = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'friend_groups'

    def __str__(self):
        return f'{self.user.username}: {self.name}'


class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_of')
    remark = models.CharField(max_length=64, blank=True, default='')
    group = models.ForeignKey(FriendGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='friends')
    tags = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'friendships'
        unique_together = ('user', 'friend')

    def __str__(self):
        return f'{self.user.username} - {self.friend.username}'


class Blacklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blacklists'
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f'{self.user.username} blocked {self.blocked_user.username}'


class Conversation(models.Model):
    PRIVATE = 'private'
    GROUP = 'group'
    TYPE_CHOICES = [
        (PRIVATE, 'Private'),
        (GROUP, 'Group'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PRIVATE)
    name = models.CharField(max_length=128, blank=True, default='')
    avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True, default='')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_conversations')
    announcement = models.TextField(blank=True, default='')
    invite_code = models.CharField(max_length=32, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversations'

    def __str__(self):
        return f'{self.type}: {self.name or self.id}'

    def save(self, *args, **kwargs):
        if not self.invite_code and self.type == self.GROUP:
            self.invite_code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)


class GroupTransferRecord(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='transfer_records')
    old_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferred_ownership')
    new_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ownership')
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group_transfer_records'
        ordering = ['-transferred_at']

    def __str__(self):
        return f'{self.conversation.name}: {self.old_owner.username} -> {self.new_owner.username}'


class ConversationMember(models.Model):
    MEMBER = 'member'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (MEMBER, 'Member'),
        (ADMIN, 'Admin'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    nickname = models.CharField(max_length=64, blank=True, default='')
    is_pinned = models.BooleanField(default=False)
    mute = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invited_members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation_members'
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f'{self.user.username} in {self.conversation.id}'


class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    FILE = 'file'
    SYSTEM = 'system'
    TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (FILE, 'File'),
        (SYSTEM, 'System'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TEXT)
    file_url = models.CharField(max_length=512, blank=True, default='')
    file_name = models.CharField(max_length=256, blank=True, default='')
    file_size = models.IntegerField(default=0)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    mentioned_users = models.ManyToManyField(User, blank=True, related_name='mentioned_in')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_recalled = models.BooleanField(default=False)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30]}'


class FavoriteMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_messages')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorite_messages'
        unique_together = ('user', 'message')

    def __str__(self):
        return f'{self.user.username} favorited {self.message.id}'


class FriendRequest(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'friend_requests'
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user.username} -> {self.to_user.username}: {self.status}'

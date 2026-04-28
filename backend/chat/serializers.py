from rest_framework import serializers
from .models import Friendship, Conversation, ConversationMember, Message, FriendRequest, FriendGroup, FavoriteMessage, Blacklist, GroupTransferRecord
from users.serializers import UserSerializer


class FriendGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendGroup
        fields = ['id', 'name', 'created_at']


class FriendshipSerializer(serializers.ModelSerializer):
    friend = UserSerializer(read_only=True)
    group = FriendGroupSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'friend', 'remark', 'group', 'tags', 'created_at']


class GroupTransferRecordSerializer(serializers.ModelSerializer):
    old_owner = UserSerializer(read_only=True)
    new_owner = UserSerializer(read_only=True)

    class Meta:
        model = GroupTransferRecord
        fields = ['id', 'old_owner', 'new_owner', 'transferred_at']


class ConversationMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    nickname = serializers.CharField(read_only=True)

    class Meta:
        model = ConversationMember
        fields = ['id', 'user', 'role', 'nickname', 'is_pinned', 'mute', 'is_muted', 'joined_at']


class ConversationSerializer(serializers.ModelSerializer):
    members = ConversationMemberSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'name', 'avatar', 'owner', 'announcement', 'invite_code', 'members', 'created_at', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_recalled=False).last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class ReplyMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reply_to = ReplyMessageSerializer(read_only=True)
    mentioned_users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'message_type', 'file_url', 'file_name', 'file_size', 'reply_to', 'mentioned_users', 'created_at', 'edited_at', 'is_read', 'is_recalled']


class MessageCreateSerializer(serializers.ModelSerializer):
    reply_to_id = serializers.IntegerField(required=False, allow_null=True)
    mentioned_user_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    class Meta:
        model = Message
        fields = ['conversation', 'content', 'message_type', 'file_url', 'file_name', 'file_size', 'reply_to_id', 'mentioned_user_ids']


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at']


class FavoriteMessageSerializer(serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)

    class Meta:
        model = FavoriteMessage
        fields = ['id', 'message', 'created_at']


class BlacklistSerializer(serializers.ModelSerializer):
    blocked_user = UserSerializer(read_only=True)

    class Meta:
        model = Blacklist
        fields = ['id', 'blocked_user', 'created_at']

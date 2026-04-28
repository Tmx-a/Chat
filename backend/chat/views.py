from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404
import os
import uuid
from .models import (
    Friendship, Conversation, ConversationMember, Message, FriendRequest,
    FriendGroup, FavoriteMessage, Blacklist, GroupTransferRecord
)
from .serializers import (
    FriendshipSerializer, ConversationSerializer, ConversationMemberSerializer,
    MessageSerializer, MessageCreateSerializer,
    FriendRequestSerializer, FriendGroupSerializer,
    FavoriteMessageSerializer, BlacklistSerializer,
    GroupTransferRecordSerializer,
)
from users.models import User
from users.serializers import UserSerializer


class AddFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if friend == request.user:
            return Response({'error': '不能添加自己为好友'}, status=status.HTTP_400_BAD_REQUEST)

        if Blacklist.objects.filter(user=friend, blocked_user=request.user).exists():
            return Response({'error': '对方已将你加入黑名单'}, status=status.HTTP_400_BAD_REQUEST)

        exists = Friendship.objects.filter(
            Q(user=request.user, friend=friend) | Q(user=friend, friend=request.user)
        ).exists()
        if exists:
            return Response({'error': '已经是好友'}, status=status.HTTP_400_BAD_REQUEST)

        Friendship.objects.create(user=request.user, friend=friend)
        Friendship.objects.create(user=friend, friend=request.user)
        return Response({'message': '添加好友成功'}, status=status.HTTP_201_CREATED)


class DeleteFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        Friendship.objects.filter(user=request.user, friend_id=friend_id).delete()
        Friendship.objects.filter(user_id=friend_id, friend=request.user).delete()
        return Response({'message': '删除好友成功'})


class FriendListView(generics.ListAPIView):
    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Friendship.objects.filter(user=self.request.user).select_related('friend', 'group')


class SetFriendRemarkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        remark = request.data.get('remark', '')
        friendship = Friendship.objects.filter(user=request.user, friend_id=friend_id).first()
        if friendship:
            friendship.remark = remark
            friendship.save()
            return Response(FriendshipSerializer(friendship).data)
        return Response({'error': '好友关系不存在'}, status=status.HTTP_404_NOT_FOUND)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            members__user=self.request.user,
            members__is_hidden=False
        ).prefetch_related('members__user', 'messages').order_by('-members__is_pinned', '-created_at')


class CreatePrivateConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        existing = Conversation.objects.filter(
            type=Conversation.PRIVATE,
            members__user=request.user
        ).filter(
            members__user=friend
        ).first()

        if existing:
            member = ConversationMember.objects.filter(conversation=existing, user=request.user).first()
            if member and member.is_hidden:
                member.is_hidden = False
                member.save()
            serializer = ConversationSerializer(existing)
            return Response(serializer.data)

        conversation = Conversation.objects.create(type=Conversation.PRIVATE)
        ConversationMember.objects.create(conversation=conversation, user=request.user)
        ConversationMember.objects.create(conversation=conversation, user=friend)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateGroupConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '')
        member_ids = request.data.get('member_ids', [])

        conversation = Conversation.objects.create(type=Conversation.GROUP, name=name, owner=request.user)
        ConversationMember.objects.create(conversation=conversation, user=request.user)

        for uid in member_ids:
            try:
                user = User.objects.get(id=uid)
                ConversationMember.objects.create(conversation=conversation, user=user)
            except User.DoesNotExist:
                continue

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        before_id = self.request.query_params.get('before_id')
        limit = int(self.request.query_params.get('limit', 50))
        
        queryset = Message.objects.filter(
            conversation_id=conversation_id,
            conversation__members__user=self.request.user,
            is_recalled=False
        ).select_related('sender', 'reply_to').prefetch_related('mentioned_users')
        
        if before_id:
            queryset = queryset.filter(id__lt=before_id)
        
        return queryset.order_by('-created_at')[:limit]


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        reply_to_id = self.request.data.get('reply_to_id')
        mentioned_user_ids = self.request.data.get('mentioned_user_ids', [])
        
        message = serializer.save(
            sender=self.request.user,
            reply_to_id=reply_to_id if reply_to_id else None
        )
        
        if mentioned_user_ids:
            message.mentioned_users.set(mentioned_user_ids)


class MarkMessagesReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not ConversationMember.objects.filter(
            conversation=conversation,
            user=request.user
        ).exists():
            return Response({'error': '无权访问此会话'}, status=status.HTTP_403_FORBIDDEN)

        updated = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)

        return Response({
            'message': '标记成功',
            'updated_count': updated,
            'conversation_id': conversation_id,
        })


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return Response({
            'url': f"{settings.MEDIA_URL}uploads/{filename}",
            'name': file.name,
            'size': file.size,
        })


class FriendRequestListView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user)


class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if to_user == request.user:
            return Response({'error': '不能添加自己为好友'}, status=status.HTTP_400_BAD_REQUEST)

        if Blacklist.objects.filter(user=to_user, blocked_user=request.user).exists():
            return Response({'error': '对方已将你加入黑名单'}, status=status.HTTP_400_BAD_REQUEST)

        existing_friend = Friendship.objects.filter(
            Q(user=request.user, friend=to_user) | Q(user=to_user, friend=request.user)
        ).exists()
        if existing_friend:
            return Response({'error': '已经是好友'}, status=status.HTTP_400_BAD_REQUEST)

        existing_request = FriendRequest.objects.filter(
            from_user=request.user, to_user=to_user
        ).first()
        if existing_request:
            if existing_request.status == FriendRequest.PENDING:
                return Response({'error': '已发送过申请'}, status=status.HTTP_400_BAD_REQUEST)
            existing_request.status = FriendRequest.PENDING
            existing_request.save()
            return Response(FriendRequestSerializer(existing_request).data)

        reverse_request = FriendRequest.objects.filter(
            from_user=to_user, to_user=request.user, status=FriendRequest.PENDING
        ).first()
        if reverse_request:
            Friendship.objects.create(user=request.user, friend=to_user)
            Friendship.objects.create(user=to_user, friend=request.user)
            reverse_request.status = FriendRequest.ACCEPTED
            reverse_request.save()
            return Response({'message': '对方已向你发送申请，已自动成为好友'})

        friend_request = FriendRequest.objects.create(
            from_user=request.user,
            to_user=to_user
        )
        return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status=FriendRequest.PENDING
            )
        except FriendRequest.DoesNotExist:
            return Response({'error': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = FriendRequest.ACCEPTED
        friend_request.save()

        Friendship.objects.create(user=request.user, friend=friend_request.from_user)
        Friendship.objects.create(user=friend_request.from_user, friend=request.user)

        return Response({'message': '已接受好友申请'})


class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status=FriendRequest.PENDING
            )
        except FriendRequest.DoesNotExist:
            return Response({'error': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = FriendRequest.REJECTED
        friend_request.save()

        return Response({'message': '已拒绝好友申请'})


class MessageSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        messages = Message.objects.filter(
            content__icontains=query,
            conversation__members__user=request.user,
            is_recalled=False
        ).select_related('sender', 'conversation')[:50]

        return Response(MessageSerializer(messages, many=True).data)


class PinConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        member = ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=request.user
        ).first()
        if member:
            member.is_pinned = not member.is_pinned
            member.save()
            return Response({'is_pinned': member.is_pinned})
        return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)


class MuteConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        member = ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=request.user
        ).first()
        if member:
            member.mute = not member.mute
            member.save()
            return Response({'mute': member.mute})
        return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)


class HideConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        member = ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=request.user
        ).first()
        if member:
            member.is_hidden = True
            member.save()
            return Response({'message': '会话已删除'})
        return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)


class FavoriteMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message_id')
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response({'error': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = FavoriteMessage.objects.get_or_create(
            user=request.user,
            message=message
        )
        if not created:
            favorite.delete()
            return Response({'favorited': False})
        return Response({'favorited': True})


class FavoriteMessageListView(generics.ListAPIView):
    serializer_class = FavoriteMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteMessage.objects.filter(user=self.request.user).select_related('message__sender')


class ForwardMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message_id')
        target_conversation_id = request.data.get('target_conversation_id')
        
        try:
            original_message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response({'error': '原消息不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not ConversationMember.objects.filter(
            conversation_id=target_conversation_id,
            user=request.user
        ).exists():
            return Response({'error': '无权访问目标会话'}, status=status.HTTP_403_FORBIDDEN)

        new_message = Message.objects.create(
            conversation_id=target_conversation_id,
            sender=request.user,
            content=original_message.content,
            message_type=original_message.message_type,
            file_url=original_message.file_url,
            file_name=original_message.file_name,
            file_size=original_message.file_size,
        )
        return Response(MessageSerializer(new_message).data)


class GroupAnnouncementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        announcement = request.data.get('announcement', '')
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以发布公告'}, status=status.HTTP_400_BAD_REQUEST)

        member = ConversationMember.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if not member or (member.role != ConversationMember.ADMIN and conversation.owner != request.user):
            return Response({'error': '只有群主或管理员可以发布公告'}, status=status.HTTP_403_FORBIDDEN)

        conversation.announcement = announcement
        conversation.save()
        return Response(ConversationSerializer(conversation).data)


class GroupAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以设置头像'}, status=status.HTTP_400_BAD_REQUEST)

        if conversation.owner != request.user:
            return Response({'error': '只有群主可以设置群头像'}, status=status.HTTP_403_FORBIDDEN)

        if 'avatar' in request.FILES:
            conversation.avatar = request.FILES['avatar']
            conversation.save()
            return Response(ConversationSerializer(conversation).data)
        return Response({'error': '请上传头像'}, status=status.HTTP_400_BAD_REQUEST)


class SetGroupAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        member_id = request.data.get('member_id')
        is_admin = request.data.get('is_admin', True)
        
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以设置管理员'}, status=status.HTTP_400_BAD_REQUEST)

        if conversation.owner != request.user:
            return Response({'error': '只有群主可以设置管理员'}, status=status.HTTP_403_FORBIDDEN)

        member = ConversationMember.objects.filter(
            conversation=conversation,
            user_id=member_id
        ).first()
        
        if member:
            member.role = ConversationMember.ADMIN if is_admin else ConversationMember.MEMBER
            member.save()
            return Response(ConversationMemberSerializer(member).data)
        return Response({'error': '成员不存在'}, status=status.HTTP_404_NOT_FOUND)


class JoinGroupByInviteCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get('invite_code', '').upper()
        inviter_id = request.data.get('inviter_id')
        
        conversation = Conversation.objects.filter(
            invite_code=invite_code,
            type=Conversation.GROUP
        ).first()
        
        if not conversation:
            return Response({'error': '邀请码无效'}, status=status.HTTP_404_NOT_FOUND)

        member, created = ConversationMember.objects.get_or_create(
            conversation=conversation,
            user=request.user,
            defaults={'invited_by_id': inviter_id} if inviter_id else {}
        )
        
        if created:
            inviter = None
            if inviter_id:
                try:
                    inviter = User.objects.get(id=inviter_id)
                except User.DoesNotExist:
                    pass
            
            if inviter:
                system_content = f"{inviter.username} 邀请 {request.user.username} 加入了群聊"
            else:
                system_content = f"{request.user.username} 通过邀请码加入了群聊"
            
            system_message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=system_content,
                message_type=Message.SYSTEM
            )
            
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation.id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': system_message.id,
                        'conversation_id': conversation.id,
                        'sender': {
                            'id': request.user.id,
                            'username': request.user.username,
                            'avatar': request.user.avatar.url if request.user.avatar else '',
                        },
                        'content': system_content,
                        'message_type': 'system',
                        'created_at': system_message.created_at.isoformat(),
                        'is_read': False,
                        'is_recalled': False,
                    }
                }
            )
            
            return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)
        return Response({'message': '你已经是群成员'})


class KickGroupMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以踢人'}, status=status.HTTP_400_BAD_REQUEST)
        
        requester = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if not requester:
            return Response({'error': '你不是群成员'}, status=status.HTTP_403_FORBIDDEN)
        
        if requester.role not in [ConversationMember.ADMIN] and conversation.owner != request.user:
            return Response({'error': '只有群主或管理员可以踢人'}, status=status.HTTP_403_FORBIDDEN)
        
        member_id = request.data.get('member_id')
        target_member = ConversationMember.objects.filter(
            conversation=conversation, user_id=member_id
        ).first()
        
        if not target_member:
            return Response({'error': '成员不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        if target_member.role == 'owner':
            return Response({'error': '不能踢出群主'}, status=status.HTTP_400_BAD_REQUEST)
        
        if target_member.role == 'admin' and conversation.owner != request.user:
            return Response({'error': '只有群主可以踢出管理员'}, status=status.HTTP_403_FORBIDDEN)
        
        target_member.delete()
        return Response({'message': '已移除成员'})


class LeaveGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以退出'}, status=status.HTTP_400_BAD_REQUEST)
        
        if conversation.owner == request.user:
            return Response({'error': '群主不能退出群聊，请先转让群主或解散群聊'}, status=status.HTTP_400_BAD_REQUEST)
        
        member = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if not member:
            return Response({'error': '你不是群成员'}, status=status.HTTP_403_FORBIDDEN)
        
        member.delete()
        return Response({'message': '已退出群聊'})


class DissolveGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以解散'}, status=status.HTTP_400_BAD_REQUEST)
        
        if conversation.owner != request.user:
            return Response({'error': '只有群主可以解散群聊'}, status=status.HTTP_403_FORBIDDEN)
        
        ConversationMember.objects.filter(conversation=conversation).delete()
        Message.objects.filter(conversation=conversation).delete()
        conversation.delete()
        return Response({'message': '群聊已解散'})


class UpdateGroupNameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以修改名称'}, status=status.HTTP_400_BAD_REQUEST)
        
        member = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if not member:
            return Response({'error': '你不是群成员'}, status=status.HTTP_403_FORBIDDEN)
        
        if member.role not in [ConversationMember.ADMIN] and conversation.owner != request.user:
            return Response({'error': '只有群主或管理员可以修改群名称'}, status=status.HTTP_403_FORBIDDEN)
        
        new_name = request.data.get('name', '').strip()
        if not new_name:
            return Response({'error': '群名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_name) > 50:
            return Response({'error': '群名称不能超过50个字符'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation.name = new_name
        conversation.save()
        return Response(ConversationSerializer(conversation).data)


class TransferGroupOwnerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以转让'}, status=status.HTTP_400_BAD_REQUEST)
        
        if conversation.owner != request.user:
            return Response({'error': '只有群主可以转让群主身份'}, status=status.HTTP_403_FORBIDDEN)
        
        new_owner_id = request.data.get('new_owner_id')
        if not new_owner_id:
            return Response({'error': '请指定新群主'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_owner_member = ConversationMember.objects.filter(
            conversation=conversation, user_id=new_owner_id
        ).first()
        
        if not new_owner_member:
            return Response({'error': '该用户不是群成员'}, status=status.HTTP_404_NOT_FOUND)
        
        old_owner = conversation.owner
        old_owner_member = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if old_owner_member:
            old_owner_member.role = ConversationMember.MEMBER
            old_owner_member.save()
        
        if new_owner_member.role == ConversationMember.ADMIN:
            new_owner_member.role = ConversationMember.MEMBER
            new_owner_member.save()
        
        conversation.owner = new_owner_member.user
        conversation.save()
        
        GroupTransferRecord.objects.create(
            conversation=conversation,
            old_owner=old_owner,
            new_owner=new_owner_member.user
        )
        
        return Response(ConversationSerializer(conversation).data)


class GroupTransferRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊有转让记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        records = GroupTransferRecord.objects.filter(conversation=conversation)[:10]
        return Response(GroupTransferRecordSerializer(records, many=True).data)


class SetFriendTagsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_id):
        friendship = Friendship.objects.filter(user=request.user, friend_id=friend_id).first()
        if not friendship:
            return Response({'error': '好友关系不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        tags = request.data.get('tags', '')
        if isinstance(tags, list):
            tags = ','.join(tags)
        friendship.tags = tags[:256]
        friendship.save()
        return Response(FriendshipSerializer(friendship).data)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        from users.models import User
        user = get_object_or_404(User, id=user_id)
        
        friendship = Friendship.objects.filter(user=request.user, friend=user).first()
        
        data = {
            'user': UserSerializer(user).data,
            'is_friend': friendship is not None,
            'remark': friendship.remark if friendship else '',
            'tags': friendship.tags.split(',') if friendship and friendship.tags else [],
        }
        return Response(data)


class BlacklistView(generics.ListAPIView):
    serializer_class = BlacklistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Blacklist.objects.filter(user=self.request.user)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            blocked_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if blocked_user == request.user:
            return Response({'error': '不能拉黑自己'}, status=status.HTTP_400_BAD_REQUEST)

        Friendship.objects.filter(
            Q(user=request.user, friend=blocked_user) | Q(user=blocked_user, friend=request.user)
        ).delete()

        blocked, created = Blacklist.objects.get_or_create(
            user=request.user,
            blocked_user=blocked_user
        )
        if not created:
            blocked.delete()
            return Response({'blocked': False})
        
        ConversationMember.objects.filter(
            conversation__type=Conversation.PRIVATE,
            conversation__members__user=request.user
        ).filter(
            conversation__members__user=blocked_user
        ).update(is_hidden=True)
        
        return Response({'blocked': True})


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        deleted, _ = Blacklist.objects.filter(
            user=request.user,
            blocked_user_id=user_id
        ).delete()
        
        if deleted:
            return Response({'message': '已取消拉黑'})
        return Response({'error': '该用户不在黑名单中'}, status=status.HTTP_404_NOT_FOUND)


class FriendGroupListView(generics.ListAPIView):
    serializer_class = FriendGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FriendGroup.objects.filter(user=self.request.user)


class CreateFriendGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '')
        if not name:
            return Response({'error': '分组名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        group = FriendGroup.objects.create(user=request.user, name=name)
        return Response(FriendGroupSerializer(group).data, status=status.HTTP_201_CREATED)


class SetFriendGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        group_id = request.data.get('group_id')
        
        friendship = Friendship.objects.filter(user=request.user, friend_id=friend_id).first()
        if not friendship:
            return Response({'error': '好友关系不存在'}, status=status.HTTP_404_NOT_FOUND)

        if group_id:
            group = FriendGroup.objects.filter(id=group_id, user=request.user).first()
            if not group:
                return Response({'error': '分组不存在'}, status=status.HTTP_404_NOT_FOUND)
            friendship.group = group
        else:
            friendship.group = None
        friendship.save()
        return Response(FriendshipSerializer(friendship).data)


class EditMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response({'error': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        if message.sender != request.user:
            return Response({'error': '只能编辑自己的消息'}, status=status.HTTP_403_FORBIDDEN)
        
        if message.is_recalled:
            return Response({'error': '已撤回的消息不能编辑'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.utils import timezone
        time_diff = (timezone.now() - message.created_at).total_seconds()
        if time_diff > 120:
            return Response({'error': '只能编辑2分钟内的消息'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_content = request.data.get('content', '').strip()
        if not new_content:
            return Response({'error': '消息内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        message.content = new_content
        message.edited_at = timezone.now()
        message.save()
        return Response(MessageSerializer(message).data)


class MuteGroupMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以禁言'}, status=status.HTTP_400_BAD_REQUEST)
        
        requester = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if not requester:
            return Response({'error': '你不是群成员'}, status=status.HTTP_403_FORBIDDEN)
        
        if requester.role not in [ConversationMember.ADMIN] and conversation.owner != request.user:
            return Response({'error': '只有群主或管理员可以禁言'}, status=status.HTTP_403_FORBIDDEN)
        
        member_id = request.data.get('member_id')
        is_muted = request.data.get('is_muted', True)
        
        target_member = ConversationMember.objects.filter(
            conversation=conversation, user_id=member_id
        ).first()
        
        if not target_member:
            return Response({'error': '成员不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        if target_member.role == 'owner':
            return Response({'error': '不能禁言群主'}, status=status.HTTP_400_BAD_REQUEST)
        
        if target_member.role == 'admin' and conversation.owner != request.user:
            return Response({'error': '只有群主可以禁言管理员'}, status=status.HTTP_403_FORBIDDEN)
        
        target_member.is_muted = is_muted
        target_member.save()
        return Response({'message': '已禁言' if is_muted else '已解除禁言', 'is_muted': is_muted})


class SetGroupNicknameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if conversation.type != Conversation.GROUP:
            return Response({'error': '只有群聊可以设置昵称'}, status=status.HTTP_400_BAD_REQUEST)
        
        member = ConversationMember.objects.filter(
            conversation=conversation, user=request.user
        ).first()
        
        if not member:
            return Response({'error': '你不是群成员'}, status=status.HTTP_403_FORBIDDEN)
        
        nickname = request.data.get('nickname', '').strip()[:64]
        member.nickname = nickname
        member.save()
        return Response(ConversationMemberSerializer(member).data)

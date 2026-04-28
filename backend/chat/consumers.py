import json
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from users.models import User
from chat.models import Conversation, ConversationMember, Message, Friendship, Blacklist


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        await self.set_user_online(True)

        await self.channel_layer.group_add(
            f'user_{self.user.id}',
            self.channel_name
        )

        await self.accept()

        conversations = await self.get_user_conversations()
        for conv_id in conversations:
            await self.channel_layer.group_add(
                f'chat_{conv_id}',
                self.channel_name
            )

        await self.broadcast_user_status(True)

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and not self.user.is_anonymous:
            await self.set_user_online(False)

            await self.broadcast_user_status(False)

            conversations = await self.get_user_conversations()
            for conv_id in conversations:
                await self.channel_layer.group_discard(
                    f'chat_{conv_id}',
                    self.channel_name
                )

            await self.channel_layer.group_discard(
                f'user_{self.user.id}',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            conversation_id = data.get('conversation_id')
            content = data.get('content', '')
            msg_type = data.get('message_type', 'text')
            file_url = data.get('file_url', '')
            file_name = data.get('file_name', '')
            file_size = data.get('file_size', 0)
            reply_to_id = data.get('reply_to_id')
            mentioned_user_ids = data.get('mentioned_user_ids', [])
            client_message_id = data.get('client_message_id')

            blocked = await self.check_blocked(conversation_id)
            if blocked:
                await self.send(text_data=json.dumps({
                    'type': 'message_error',
                    'client_message_id': client_message_id,
                    'error': 'blocked',
                    'message': '对方已将您加入黑名单，无法发送消息',
                }))
                return

            message = await self.save_message(
                conversation_id, content, msg_type, file_url, file_name, file_size,
                reply_to_id, mentioned_user_ids
            )

            if message:
                message['client_message_id'] = client_message_id
                await self.channel_layer.group_send(
                    f'chat_{conversation_id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                    }
                )
                member_ids = await self.get_conversation_member_ids(conversation_id)
                for member_id in member_ids:
                    if member_id != self.user.id:
                        await self.channel_layer.group_send(
                            f'user_{member_id}',
                            {
                                'type': 'new_message_notification',
                                'message': message,
                                'conversation_id': conversation_id,
                            }
                        )

        elif message_type == 'mark_read':
            conversation_id = data.get('conversation_id')
            result = await self.mark_messages_read(conversation_id)
            if result:
                await self.channel_layer.group_send(
                    f'chat_{conversation_id}',
                    {
                        'type': 'messages_read',
                        'conversation_id': conversation_id,
                        'reader_id': self.user.id,
                    }
                )

        elif message_type == 'typing':
            conversation_id = data.get('conversation_id')
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                f'chat_{conversation_id}',
                {
                    'type': 'typing_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing,
                }
            )

        elif message_type == 'recall_message':
            message_id = data.get('message_id')
            result = await self.recall_message(message_id)
            if result:
                await self.channel_layer.group_send(
                    f'chat_{result["conversation_id"]}',
                    {
                        'type': 'message_recalled',
                        'message_id': message_id,
                        'conversation_id': result['conversation_id'],
                        'recalled_by': self.user.id,
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online'],
        }))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'conversation_id': event['conversation_id'],
            'reader_id': event['reader_id'],
        }))

    async def typing_status(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def message_recalled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_recalled',
            'message_id': event['message_id'],
            'conversation_id': event['conversation_id'],
            'recalled_by': event['recalled_by'],
        }))

    async def new_message_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'message': event['message'],
            'conversation_id': event['conversation_id'],
        }))

    async def broadcast_user_status(self, is_online):
        friend_ids = await self.get_friend_ids()
        for friend_id in friend_ids:
            await self.channel_layer.group_send(
                f'user_{friend_id}',
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_online': is_online,
                }
            )

    @database_sync_to_async
    def set_user_online(self, online):
        self.user.is_online = online
        self.user.save(update_fields=['is_online'])

    @database_sync_to_async
    def get_user_conversations(self):
        return list(ConversationMember.objects.filter(
            user=self.user
        ).values_list('conversation_id', flat=True))

    @database_sync_to_async
    def get_friend_ids(self):
        friendships = Friendship.objects.filter(user=self.user)
        return list(friendships.values_list('friend_id', flat=True))

    @database_sync_to_async
    def get_conversation_member_ids(self, conversation_id):
        return list(ConversationMember.objects.filter(
            conversation_id=conversation_id
        ).values_list('user_id', flat=True))

    @database_sync_to_async
    def check_blocked(self, conversation_id):
        member_ids = list(ConversationMember.objects.filter(
            conversation_id=conversation_id
        ).values_list('user_id', flat=True))
        
        for member_id in member_ids:
            if member_id != self.user.id:
                if Blacklist.objects.filter(user_id=member_id, blocked_user_id=self.user.id).exists():
                    return True
        return False

    @database_sync_to_async
    def save_message(self, conversation_id, content, message_type, file_url='', file_name='', file_size=0, reply_to_id=None, mentioned_user_ids=None):
        if mentioned_user_ids is None:
            mentioned_user_ids = []
            
        is_member = ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=self.user
        ).exists()

        if not is_member:
            return None

        message = Message.objects.create(
            conversation_id=conversation_id,
            sender=self.user,
            content=content,
            message_type=message_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            reply_to_id=reply_to_id if reply_to_id else None,
        )
        
        if mentioned_user_ids:
            message.mentioned_users.set(mentioned_user_ids)
        
        reply_to_data = None
        if message.reply_to:
            reply_to_data = {
                'id': message.reply_to.id,
                'content': message.reply_to.content,
                'sender': {
                    'id': message.reply_to.sender.id,
                    'username': message.reply_to.sender.username,
                },
                'created_at': message.reply_to.created_at.isoformat(),
            }
        
        mentioned_users_data = []
        for u in message.mentioned_users.all():
            mentioned_users_data.append({
                'id': u.id,
                'username': u.username,
            })
        
        return {
            'id': message.id,
            'conversation_id': conversation_id,
            'sender': {
                'id': self.user.id,
                'username': self.user.username,
                'avatar': self.user.avatar.url if self.user.avatar else '',
            },
            'content': message.content,
            'message_type': message.message_type,
            'file_url': message.file_url,
            'file_name': message.file_name,
            'file_size': message.file_size,
            'reply_to': reply_to_data,
            'mentioned_users': mentioned_users_data,
            'created_at': message.created_at.isoformat(),
            'is_read': message.is_read,
            'is_recalled': message.is_recalled,
        }

    @database_sync_to_async
    def mark_messages_read(self, conversation_id):
        is_member = ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=self.user
        ).exists()

        if not is_member:
            return None

        updated = Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)

        return {'updated': updated, 'conversation_id': conversation_id}

    @database_sync_to_async
    def recall_message(self, message_id):
        try:
            message = Message.objects.get(id=message_id, sender=self.user, is_recalled=False)
            time_diff = datetime.now(message.created_at.tzinfo) - message.created_at
            if time_diff > timedelta(minutes=2):
                return None
            message.is_recalled = True
            message.content = ''
            message.save()
            return {'conversation_id': message.conversation_id}
        except Message.DoesNotExist:
            return None

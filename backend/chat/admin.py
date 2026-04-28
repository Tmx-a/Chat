from django.contrib import admin
from .models import Friendship, Conversation, ConversationMember, Message

admin.site.register(Friendship)
admin.site.register(Conversation)
admin.site.register(ConversationMember)
admin.site.register(Message)

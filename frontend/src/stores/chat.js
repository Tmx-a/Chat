import { defineStore } from "pinia";
import { ref } from "vue";
import { chatApi } from "../api/modules";

export const useChatStore = defineStore("chat", () => {
  const conversations = ref([]);
  const currentConversation = ref(null);
  const messages = ref({});
  const friends = ref([]);
  const typingUsers = ref({});
  const friendRequests = ref([]);
  const hasMoreMessages = ref({});
  const loadingMessages = ref({});

  async function fetchConversations() {
    const res = await chatApi.getConversations();
    conversations.value = res.data;
  }

  async function fetchMessages(conversationId, beforeId = null) {
    if (loadingMessages.value[conversationId]) return;
    loadingMessages.value[conversationId] = true;

    try {
      const res = await chatApi.getMessages(conversationId, beforeId);
      const newMessages = res.data.reverse();

      if (beforeId) {
        const existingIds = new Set(
          (messages.value[conversationId] || []).map((m) => m.id),
        );
        const uniqueNewMessages = newMessages.filter(
          (m) => !existingIds.has(m.id),
        );
        messages.value[conversationId] = [
          ...uniqueNewMessages,
          ...(messages.value[conversationId] || []),
        ];
      } else {
        messages.value[conversationId] = newMessages;
      }

      hasMoreMessages.value[conversationId] = newMessages.length === 50;
      currentConversation.value = conversationId;
    } finally {
      loadingMessages.value[conversationId] = false;
    }
  }

  async function fetchFriends() {
    const res = await chatApi.getFriends();
    friends.value = res.data;
  }

  async function addFriend(friendId) {
    await chatApi.addFriend(friendId);
    await fetchFriends();
  }

  async function startPrivateChat(friendId) {
    const res = await chatApi.createPrivateConversation(friendId);
    await fetchConversations();
    return res.data;
  }

  async function createGroup(name, memberIds) {
    const res = await chatApi.createGroupConversation(name, memberIds);
    await fetchConversations();
    return res.data;
  }

  function addMessage(conversationId, message) {
    if (!messages.value[conversationId]) {
      messages.value[conversationId] = [];
    }
    const exists = messages.value[conversationId].some(
      (m) =>
        m.id === message.id ||
        (m.client_message_id &&
          m.client_message_id === message.client_message_id),
    );
    if (!exists) {
      messages.value[conversationId].push(message);
    }
  }

  function updateMessage(conversationId, clientMessageId, newMessage) {
    if (!messages.value[conversationId]) return;
    const index = messages.value[conversationId].findIndex(
      (m) => m.client_message_id === clientMessageId,
    );
    if (index !== -1) {
      messages.value[conversationId][index] = {
        ...newMessage,
        client_message_id: clientMessageId,
        _sending: false,
        _error: false,
      };
    }
  }

  function removeTempMessage(conversationId, tempId) {
    if (!messages.value[conversationId]) return;
    messages.value[conversationId] = messages.value[conversationId].filter(
      (m) => m.id !== tempId,
    );
  }

  function updateFriendStatus(userId, isOnline) {
    const friendship = friends.value.find((f) => f.friend.id === userId);
    if (friendship) {
      friendship.friend.is_online = isOnline;
    }
  }

  function markMessagesAsRead(conversationId, readerId) {
    const msgs = messages.value[conversationId];
    if (msgs) {
      msgs.forEach((msg) => {
        if (msg.sender.id !== readerId) {
          msg.is_read = true;
        }
      });
    }
  }

  function setTypingStatus(userId, username, isTyping) {
    if (!typingUsers.value[currentConversation.value]) {
      typingUsers.value[currentConversation.value] = {};
    }
    if (isTyping) {
      typingUsers.value[currentConversation.value][userId] = username;
    } else {
      delete typingUsers.value[currentConversation.value][userId];
    }
  }

  function recallMessage(messageId) {
    for (const convId in messages.value) {
      const msg = messages.value[convId].find((m) => m.id === messageId);
      if (msg) {
        msg.is_recalled = true;
        msg.content = "";
        break;
      }
    }
  }

  async function fetchFriendRequests() {
    try {
      const res = await chatApi.getFriendRequests();
      friendRequests.value = res.data;
    } catch (e) {
      console.error("获取好友申请失败", e);
    }
  }

  function updateConversationMember(conversationId, memberId, updates) {
    const conv = conversations.value.find((c) => c.id === conversationId);
    if (conv && conv.members) {
      const member = conv.members.find((m) => m.user.id === memberId);
      if (member) {
        Object.assign(member, updates);
      }
    }
  }

  function removeConversation(conversationId) {
    conversations.value = conversations.value.filter(
      (c) => c.id !== conversationId,
    );
    if (currentConversation.value === conversationId) {
      currentConversation.value = null;
    }
    delete messages.value[conversationId];
  }

  function removeFriend(friendId) {
    friends.value = friends.value.filter((f) => f.friend.id !== friendId);
  }

  function handleNewMessageNotification(message, conversationId) {
    addMessage(conversationId, message);

    const convIndex = conversations.value.findIndex(
      (c) => c.id === conversationId,
    );
    if (convIndex !== -1) {
      const conv = conversations.value[convIndex];
      conv.last_message = message;
      if (currentConversation.value !== conversationId) {
        conv.unread_count = (conv.unread_count || 0) + 1;
      }
      conversations.value.splice(convIndex, 1);
      conversations.value.unshift(conv);
    }
  }

  function clearUnreadCount(conversationId) {
    const conv = conversations.value.find((c) => c.id === conversationId);
    if (conv) {
      conv.unread_count = 0;
    }
  }

  function updateConversationLastMessage(conversationId, message) {
    const conv = conversations.value.find((c) => c.id === conversationId);
    if (conv) {
      conv.last_message = message;
    }
  }

  return {
    conversations,
    currentConversation,
    messages,
    friends,
    typingUsers,
    friendRequests,
    hasMoreMessages,
    loadingMessages,
    fetchConversations,
    fetchMessages,
    fetchFriends,
    addFriend,
    startPrivateChat,
    createGroup,
    addMessage,
    updateMessage,
    removeTempMessage,
    updateFriendStatus,
    markMessagesAsRead,
    setTypingStatus,
    recallMessage,
    fetchFriendRequests,
    updateConversationMember,
    removeConversation,
    removeFriend,
    handleNewMessageNotification,
    clearUnreadCount,
    updateConversationLastMessage,
  };
});

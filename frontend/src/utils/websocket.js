import { useUserStore } from "../stores/user";
import { useChatStore } from "../stores/chat";

class WebSocketManager {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.typingTimeout = null;
    this.messageQueue = [];
    this.messageCallbacks = new Map();
    this.messageIdCounter = 0;
  }

  connect() {
    const userStore = useUserStore();
    if (!userStore.token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    let url = `${protocol}//${host}/ws/chat/?token=${userStore.token}`;
    if (userStore.sessionId) {
      url += `&session_id=${userStore.sessionId}`;
    }

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("WebSocket 连接成功");
      this.reconnectAttempts = 0;
      this.flushMessageQueue();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const chatStore = useChatStore();

      if (data.type === "chat_message") {
        const userStore = useUserStore();
        if (
          data.client_message_id &&
          data.message.sender.id === userStore.user?.id
        ) {
          chatStore.updateMessage(
            data.message.conversation_id,
            data.client_message_id,
            data.message,
          );
        } else {
          chatStore.addMessage(data.message.conversation_id, data.message);
        }
        this.showNotification(data.message);
        this.playNotificationSoundIfNeeded(data.message, chatStore);
        this.resolveMessageCallback(data.client_message_id, data.message);
      } else if (data.type === "new_message_notification") {
        chatStore.handleNewMessageNotification(
          data.message,
          data.conversation_id,
        );
        this.showNotification(data.message);
        this.playNotificationSoundIfNeeded(data.message, chatStore);
      } else if (data.type === "user_status") {
        chatStore.updateFriendStatus(data.user_id, data.is_online);
      } else if (data.type === "messages_read") {
        chatStore.markMessagesAsRead(data.conversation_id, data.reader_id);
      } else if (data.type === "typing_status") {
        chatStore.setTypingStatus(data.user_id, data.username, data.is_typing);
      } else if (data.type === "message_recalled") {
        chatStore.recallMessage(data.message_id);
      } else if (data.type === "message_error") {
        this.rejectMessageCallback(data.client_message_id, {
          error: data.error,
          message: data.message,
        });
      }
    };

    this.ws.onclose = () => {
      console.log("WebSocket 连接关闭");
      this.tryReconnect();
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket 错误:", error);
    };
  }

  tryReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(
          `尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
        );
        this.connect();
      }, this.reconnectInterval);
    }
  }

  generateMessageId() {
    return `msg_${Date.now()}_${++this.messageIdCounter}`;
  }

  flushMessageQueue() {
    while (
      this.messageQueue.length > 0 &&
      this.ws?.readyState === WebSocket.OPEN
    ) {
      const { data, clientMessageId, resolve, reject } =
        this.messageQueue.shift();
      if (resolve) {
        this.messageCallbacks.set(clientMessageId, { resolve, reject });
      }
      this.ws.send(JSON.stringify(data));
    }
  }

  resolveMessageCallback(clientMessageId, message) {
    const callback = this.messageCallbacks.get(clientMessageId);
    if (callback) {
      callback.resolve(message);
      this.messageCallbacks.delete(clientMessageId);
    }
  }

  rejectMessageCallback(clientMessageId, error) {
    const callback = this.messageCallbacks.get(clientMessageId);
    if (callback) {
      callback.reject(error);
      this.messageCallbacks.delete(clientMessageId);
    }
  }

  sendMessage(
    conversationId,
    content,
    messageType = "text",
    fileUrl = "",
    fileName = "",
    fileSize = 0,
    replyToId = null,
    mentionedUserIds = [],
  ) {
    return new Promise((resolve, reject) => {
      const clientMessageId = this.generateMessageId();
      const data = {
        type: "chat_message",
        client_message_id: clientMessageId,
        conversation_id: conversationId,
        content,
        message_type: messageType,
        file_url: fileUrl,
        file_name: fileName,
        file_size: fileSize,
        reply_to_id: replyToId,
        mentioned_user_ids: mentionedUserIds,
      };

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.messageCallbacks.set(clientMessageId, { resolve, reject });
        this.ws.send(JSON.stringify(data));
      } else {
        this.messageQueue.push({ data, clientMessageId, resolve, reject });
      }
    });
  }

  sendMessageWithId(
    conversationId,
    content,
    clientMessageId,
    messageType = "text",
    fileUrl = "",
    fileName = "",
    fileSize = 0,
    replyToId = null,
    mentionedUserIds = [],
  ) {
    return new Promise((resolve, reject) => {
      const data = {
        type: "chat_message",
        client_message_id: clientMessageId,
        conversation_id: conversationId,
        content,
        message_type: messageType,
        file_url: fileUrl,
        file_name: fileName,
        file_size: fileSize,
        reply_to_id: replyToId,
        mentioned_user_ids: mentionedUserIds,
      };

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.messageCallbacks.set(clientMessageId, { resolve, reject });
        this.ws.send(JSON.stringify(data));
      } else {
        this.messageQueue.push({ data, clientMessageId, resolve, reject });
      }
    });
  }

  markRead(conversationId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "mark_read",
          conversation_id: conversationId,
        }),
      );
    }
  }

  sendTyping(conversationId, isTyping) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "typing",
          conversation_id: conversationId,
          is_typing: isTyping,
        }),
      );
    }
  }

  recallMessage(messageId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "recall_message",
          message_id: messageId,
        }),
      );
    }
  }

  showNotification(message) {
    const userStore = useUserStore();
    if (message.sender.id === userStore.user?.id) return;

    if (
      document.hidden &&
      "Notification" in window &&
      Notification.permission === "granted"
    ) {
      new Notification("新消息", {
        body: `${message.sender.username}: ${message.content.substring(0, 50)}`,
        icon: "/favicon.ico",
      });
    }
  }

  playNotificationSoundIfNeeded(message, chatStore) {
    const userStore = useUserStore();
    if (message.sender.id === userStore.user?.id) return;
    if (
      chatStore.currentConversation === message.conversation_id &&
      !document.hidden
    )
      return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 800;
      gain.gain.value = 0.1;
      osc.start();
      osc.stop(ctx.currentTime + 0.1);
    } catch (e) {}
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  reconnect() {
    this.disconnect();
    this.connect();
  }
}

export const wsManager = new WebSocketManager();

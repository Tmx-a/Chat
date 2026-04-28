import api from ".";

export const userApi = {
  register(data) {
    return api.post("/users/register/", data);
  },
  login(data) {
    return api.post("/users/login/", data);
  },
  logout() {
    return api.post("/users/logout/");
  },
  getProfile() {
    return api.get("/users/profile/");
  },
  getUsers() {
    return api.get("/users/list/");
  },
  getOnlineUsers() {
    return api.get("/users/online/");
  },
  updateProfile(data) {
    return api.patch("/users/profile/", data);
  },
  changePassword(data) {
    return api.post("/users/change-password/", data);
  },
  deleteAccount() {
    return api.delete("/users/account/");
  },
  searchUsers(query) {
    return api.get(`/users/search/?q=${encodeURIComponent(query)}`);
  },
  getSessions() {
    return api.get("/users/sessions/");
  },
  kickSession(sessionId) {
    return api.delete(`/users/sessions/${sessionId}/kick/`);
  },
  logoutAllOther() {
    return api.post("/users/sessions/logout-all/");
  },
};

export const chatApi = {
  addFriend(friendId) {
    return api.post("/chat/friends/add/", { friend_id: friendId });
  },
  getFriends() {
    return api.get("/chat/friends/");
  },
  deleteFriend(friendId) {
    return api.post("/chat/friends/delete/", { friend_id: friendId });
  },
  setFriendRemark(friendId, remark) {
    return api.post("/chat/friends/remark/", { friend_id: friendId, remark });
  },
  getFriendGroups() {
    return api.get("/chat/friends/groups/");
  },
  createFriendGroup(name) {
    return api.post("/chat/friends/groups/create/", { name });
  },
  setFriendGroup(friendId, groupId) {
    return api.post("/chat/friends/groups/set/", {
      friend_id: friendId,
      group_id: groupId,
    });
  },
  getConversations() {
    return api.get("/chat/conversations/");
  },
  createPrivateConversation(friendId) {
    return api.post("/chat/conversations/private/", { friend_id: friendId });
  },
  createGroupConversation(name, memberIds) {
    return api.post("/chat/conversations/group/", {
      name,
      member_ids: memberIds,
    });
  },
  getMessages(conversationId, beforeId = null, limit = 50) {
    let url = `/chat/conversations/${conversationId}/messages/?limit=${limit}`;
    if (beforeId) url += `&before_id=${beforeId}`;
    return api.get(url);
  },
  sendMessage(data) {
    return api.post("/chat/messages/", data);
  },
  markMessagesRead(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/mark-read/`);
  },
  uploadFile(formData) {
    return api.post("/chat/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getFriendRequests() {
    return api.get("/chat/friend-requests/");
  },
  sendFriendRequest(toUserId) {
    return api.post("/chat/friend-requests/send/", { to_user_id: toUserId });
  },
  acceptFriendRequest(requestId) {
    return api.post(`/chat/friend-requests/${requestId}/accept/`);
  },
  rejectFriendRequest(requestId) {
    return api.post(`/chat/friend-requests/${requestId}/reject/`);
  },
  searchMessages(query) {
    return api.get(`/chat/messages/search/?q=${encodeURIComponent(query)}`);
  },
  pinConversation(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/pin/`);
  },
  muteConversation(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/mute/`);
  },
  hideConversation(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/hide/`);
  },
  favoriteMessage(messageId) {
    return api.post("/chat/messages/favorite/", { message_id: messageId });
  },
  getFavoriteMessages() {
    return api.get("/chat/messages/favorites/");
  },
  forwardMessage(messageId, targetConversationId) {
    return api.post("/chat/messages/forward/", {
      message_id: messageId,
      target_conversation_id: targetConversationId,
    });
  },
  setGroupAnnouncement(conversationId, announcement) {
    return api.post(`/chat/conversations/${conversationId}/announcement/`, {
      announcement,
    });
  },
  uploadGroupAvatar(conversationId, formData) {
    return api.post(`/chat/conversations/${conversationId}/avatar/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  setGroupAdmin(conversationId, memberId, isAdmin) {
    return api.post(`/chat/conversations/${conversationId}/admin/`, {
      member_id: memberId,
      is_admin: isAdmin,
    });
  },
  joinGroupByInviteCode(inviteCode) {
    return api.post("/chat/conversations/join/", { invite_code: inviteCode });
  },
  kickGroupMember(conversationId, memberId) {
    return api.post(`/chat/conversations/${conversationId}/kick/`, {
      member_id: memberId,
    });
  },
  leaveGroup(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/leave/`);
  },
  dissolveGroup(conversationId) {
    return api.post(`/chat/conversations/${conversationId}/dissolve/`);
  },
  updateGroupName(conversationId, name) {
    return api.post(`/chat/conversations/${conversationId}/name/`, { name });
  },
  transferGroupOwner(conversationId, newOwnerId) {
    return api.post(`/chat/conversations/${conversationId}/transfer/`, {
      new_owner_id: newOwnerId,
    });
  },
  muteGroupMember(conversationId, memberId, isMuted) {
    return api.post(`/chat/conversations/${conversationId}/mute-member/`, {
      member_id: memberId,
      is_muted: isMuted,
    });
  },
  setGroupNickname(conversationId, nickname) {
    return api.post(`/chat/conversations/${conversationId}/nickname/`, {
      nickname,
    });
  },
  editMessage(messageId, content) {
    return api.post(`/chat/messages/${messageId}/edit/`, { content });
  },
  getTransferRecords(conversationId) {
    return api.get(`/chat/conversations/${conversationId}/transfer-records/`);
  },
  setFriendTags(friendId, tags) {
    return api.post(`/chat/friends/${friendId}/tags/`, { tags });
  },
  getUserProfile(userId) {
    return api.get(`/chat/users/${userId}/profile/`);
  },
  getBlacklist() {
    return api.get("/chat/blacklist/");
  },
  blockUser(userId) {
    return api.post("/chat/blacklist/block/", { user_id: userId });
  },
  unblockUser(userId) {
    return api.post("/chat/blacklist/unblock/", { user_id: userId });
  },
};

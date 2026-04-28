<template>
  <div class="chat-container" :class="{ 'dark-mode': isDarkMode }">
    <div v-if="!sidebarCollapsed && isMobile" class="mobile-overlay" @click="sidebarCollapsed = true"></div>
    <div :class="['sidebar', { expanded: isMobile && !sidebarCollapsed }]">
      <div class="sidebar-header">
        <div class="user-profile">
          <div class="avatar-wrapper" @click="showProfileEdit = true">
            <el-avatar :size="48" class="user-avatar" :src="userStore.user?.avatar || undefined">
              {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <el-dropdown trigger="click" @command="handleStatusChange" @click.stop>
              <span :class="['status-indicator-dot', userStore.user?.status || 'online']" @click.stop></span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="online">
                    <span class="status-option-dot online"></span> 🟢 在线
                  </el-dropdown-item>
                  <el-dropdown-item command="busy">
                    <span class="status-option-dot busy"></span> 🔴 忙碌
                  </el-dropdown-item>
                  <el-dropdown-item command="away">
                    <span class="status-option-dot away"></span> 🟡 离开
                  </el-dropdown-item>
                  <el-dropdown-item command="invisible">
                    <span class="status-option-dot invisible"></span> ⚫ 隐身
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="user-info">
            <h3>{{ userStore.user?.username }}</h3>
            <span class="status">{{ statusText }}</span>
          </div>
        </div>
        <el-dropdown trigger="click" @command="handleCommand">
          <el-button circle class="menu-btn">
            <el-icon :size="20"><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="addFriend">
                <el-icon><Plus /></el-icon>添加好友
              </el-dropdown-item>
              <el-dropdown-item command="createGroup">
                <el-icon><UserFilled /></el-icon>创建群聊
              </el-dropdown-item>
              <el-dropdown-item command="joinGroup">
                <el-icon><Connection /></el-icon>加入群聊
              </el-dropdown-item>
              <el-dropdown-item command="showFavorites">
                <el-icon><Star /></el-icon>我的收藏
              </el-dropdown-item>
              <el-dropdown-item command="showBlacklist">
                <el-icon><Hide /></el-icon>黑名单
              </el-dropdown-item>
              <el-dropdown-item command="toggleDarkMode">
                <el-icon><Moon /></el-icon>{{ isDarkMode ? '浅色模式' : '深色模式' }}
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索会话和好友..."
          :prefix-icon="Search"
          clearable
        />
        <div v-if="searchQuery && (searchConvResults.length > 0 || searchFriendResults.length > 0)" class="search-results-dropdown">
          <div v-if="searchConvResults.length > 0" class="search-group">
            <div class="search-group-title">会话</div>
            <div
              v-for="conv in searchConvResults"
              :key="'conv-' + conv.id"
              class="search-result-row"
              @click="selectConversation(conv); searchQuery = ''"
            >
              <el-avatar :size="32" :src="conv.type === 'group' ? conv.avatar : undefined">
                {{ getConversationAvatar(conv) }}
              </el-avatar>
              <span>{{ getConversationName(conv) }}</span>
            </div>
          </div>
          <div v-if="searchFriendResults.length > 0" class="search-group">
            <div class="search-group-title">好友</div>
            <div
              v-for="friendship in searchFriendResults"
              :key="'friend-' + friendship.id"
              class="search-result-row"
              @click="startChat(friendship.friend.id); searchQuery = ''"
            >
              <el-avatar :size="32" :src="friendship.friend.avatar || undefined">
                {{ friendship.friend.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span>{{ friendship.remark || friendship.friend.username }}</span>
            </div>
          </div>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="sidebar-tabs">
        <el-tab-pane name="conversations">
          <template #label>
            <span class="tab-label">
              <el-icon><ChatLineRound /></el-icon>
              消息
            </span>
          </template>
          <div class="conversation-list">
            <div v-if="initialLoading">
              <el-skeleton :rows="5" animated />
            </div>
            <template v-else>
            <div
              v-for="conv in filteredConversations"
              :key="conv.id"
              :class="['conversation-item', { active: chatStore.currentConversation === conv.id, pinned: conv.is_pinned }]"
              @click="selectConversation(conv)"
              @contextmenu.prevent="showConvContextMenu($event, conv)"
            >
              <div class="conv-avatar">
                <el-avatar :size="44" :src="conv.type === 'group' ? conv.avatar : undefined">
                  {{ getConversationAvatar(conv) }}
                </el-avatar>
                <span v-if="conv.type === 'private' && getOtherMember(conv)?.is_online" class="online-indicator"></span>
                <el-badge v-if="conv.unread_count > 0" :value="conv.unread_count" :max="99" class="unread-badge" />
              </div>
              <div class="conv-info">
                <div class="conv-header">
                  <span class="conv-name">
                    <el-icon v-if="conv.is_pinned" class="pin-icon"><Top /></el-icon>
                    {{ getConversationName(conv) }}
                  </span>
                  <span class="conv-time">{{ formatTime(conv.last_message?.created_at) }}</span>
                </div>
                <div class="conv-preview">
                  <el-icon v-if="conv.is_muted" class="mute-icon"><MuteNotification /></el-icon>
                  <span v-if="conv.last_message?.is_recalled" class="recalled-text">[消息已撤回]</span>
                  <span v-else>{{ conv.last_message?.content || '开始聊天吧...' }}</span>
                </div>
              </div>
            </div>
            <div v-if="filteredConversations.length === 0" class="empty-state">
              <el-icon :size="48"><ChatLineRound /></el-icon>
              <p>暂无会话</p>
            </div>
            </template>
          </div>
        </el-tab-pane>

        <el-tab-pane name="friends">
          <template #label>
            <span class="tab-label">
              <el-icon><User /></el-icon>
              好友
              <el-badge v-if="pendingRequestsCount > 0" :value="pendingRequestsCount" class="request-badge" />
            </span>
          </template>
          <div class="friend-list">
            <div v-if="initialLoading">
              <el-skeleton :rows="5" animated />
            </div>
            <template v-else>
            <div v-if="pendingRequests.length > 0" class="friend-requests-section">
              <div class="section-header">
                <span class="section-title">好友申请</span>
                <el-badge :value="pendingRequests.length" type="danger" />
              </div>
              <div v-for="req in pendingRequests" :key="req.id" class="request-item">
                <el-avatar :size="36" :src="req.from_user?.avatar || undefined">
                  {{ req.from_user?.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <div class="request-info">
                  <span class="request-name">{{ req.from_user?.username }}</span>
                  <span class="request-time">{{ formatTime(req.created_at) }}</span>
                </div>
                <div class="request-actions">
                  <el-button type="primary" size="small" @click="acceptRequest(req.id)">接受</el-button>
                  <el-button size="small" @click="rejectRequest(req.id)">拒绝</el-button>
                </div>
              </div>
            </div>

            <div class="friend-filter-bar">
              <el-switch v-model="showOnlineOnly" active-text="只看在线" size="small" />
              <span class="online-count">在线 {{ onlineFriendCount }}/{{ chatStore.friends.length }}</span>
            </div>

            <div class="friend-group-actions">
              <el-button size="small" text @click="showCreateFriendGroup = true">
                <el-icon><Plus /></el-icon>创建分组
              </el-button>
            </div>

            <div v-for="group in friendGroupsList" :key="group.id" class="friend-group-section">
              <div class="group-header" @click="toggleGroupExpand(group.id)">
                <el-icon><ArrowRight :class="{ 'expanded': expandedGroups[group.id] }" /></el-icon>
                <span>{{ group.name }}</span>
                <span class="group-count">{{ getGroupFriends(group.id).length }}</span>
              </div>
              <div v-show="expandedGroups[group.id]" class="group-friends">
                <div
                  v-for="friendship in getGroupFriends(group.id)"
                  :key="friendship.id"
                  class="friend-item"
                  @contextmenu.prevent="showFriendContextMenu($event, friendship)"
                >
                  <div class="friend-avatar" @click="showUserProfile(friendship.friend)">
                    <el-avatar :size="40" :src="friendship.friend.avatar || undefined">
                      {{ friendship.friend.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <span :class="['status-dot', friendship.friend.is_online ? 'online' : 'offline']"></span>
                  </div>
                  <div class="friend-info" @click="showUserProfile(friendship.friend)">
                    <span class="friend-name">{{ friendship.remark || friendship.friend.username }}</span>
                    <span class="friend-status">{{ friendship.friend.is_online ? '在线' : '离线' }}</span>
                  </div>
                  <el-button
                    type="primary"
                    size="small"
                    circle
                    class="chat-btn"
                    @click="startChat(friendship.friend.id)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <div class="friend-group-section">
              <div class="group-header" @click="toggleGroupExpand('default')">
                <el-icon><ArrowRight :class="{ 'expanded': expandedGroups['default'] }" /></el-icon>
                <span>我的好友</span>
                <span class="group-count">{{ defaultGroupFriends.length }}</span>
              </div>
              <div v-show="expandedGroups['default']" class="group-friends">
                <div
                  v-for="friendship in defaultGroupFriends"
                  :key="friendship.id"
                  class="friend-item"
                  @contextmenu.prevent="showFriendContextMenu($event, friendship)"
                >
                  <div class="friend-avatar" @click="showUserProfile(friendship.friend)">
                    <el-avatar :size="40" :src="friendship.friend.avatar || undefined">
                      {{ friendship.friend.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <span :class="['status-dot', friendship.friend.is_online ? 'online' : 'offline']"></span>
                  </div>
                  <div class="friend-info" @click="showUserProfile(friendship.friend)">
                    <span class="friend-name">{{ friendship.remark || friendship.friend.username }}</span>
                    <span class="friend-status">{{ friendship.friend.is_online ? '在线' : '离线' }}</span>
                  </div>
                  <el-button
                    type="primary"
                    size="small"
                    circle
                    class="chat-btn"
                    @click="startChat(friendship.friend.id)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <div v-if="filteredFriends.length === 0" class="empty-state">
              <el-icon :size="48"><User /></el-icon>
              <p>暂无好友</p>
            </div>
            </template>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="chat-main">
      <template v-if="chatStore.currentConversation">
        <div class="chat-header">
          <div class="chat-header-info">
            <el-button v-if="isMobile" circle class="hamburger-btn" @click="sidebarCollapsed = false">
              <el-icon><Menu /></el-icon>
            </el-button>
            <el-avatar :size="36" :src="currentConv?.type === 'group' ? currentConv?.avatar : undefined">
              {{ currentConvAvatar }}
            </el-avatar>
            <div class="chat-header-text">
              <h3>{{ currentConvName }}</h3>
              <span class="chat-status">
                {{ typingUsersText || currentConvStatus }}
              </span>
            </div>
          </div>
          <div class="chat-header-actions">
            <el-button v-if="currentConv?.type === 'group'" circle @click="showGroupSettings = true" title="群设置">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button circle @click="showSearchMessages = true">
              <el-icon><Search /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="messagesLoading" class="messages-loading">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        </div>
        <template v-else>

        <div class="message-list" ref="messageListRef" @scroll="handleScroll" @paste="handlePaste" @dragover.prevent @drop.prevent="handleDrop" style="position: relative;">
          <div v-if="isDragging" class="drag-overlay">
            <div class="drag-overlay-content">
              <el-icon :size="48"><Upload /></el-icon>
              <p>拖放文件到此处发送</p>
            </div>
          </div>
          <div v-if="loadingMore" class="loading-more">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <transition-group name="message-list" tag="div">
            <div
              v-for="(msg, index) in currentMessages"
              :key="msg.id"
              :class="['message-wrapper', msg.message_type === 'system' ? 'system' : (msg.sender.id === userStore.user?.id ? 'self' : 'other'), { consecutive: isConsecutiveMessage(currentMessages, index) }]"
              @contextmenu.prevent="msg.message_type !== 'system' && showContextMenu($event, msg)"
            >
              <template v-if="msg.message_type === 'system'">
                <div class="system-message">
                  <span>{{ msg.content }}</span>
                </div>
              </template>
              <template v-else>
                <el-avatar :size="36" class="msg-avatar" :src="msg.sender.avatar || undefined">
                  {{ msg.sender.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="message-content">
                  <div class="message-header">
                    <span class="message-sender">{{ getMemberDisplayName(msg.sender) }}</span>
                    <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
                  </div>
                  <div v-if="msg.reply_to" class="reply-preview">
                    <span class="reply-to-name">{{ msg.reply_to.sender.username }}</span>
                    <span class="reply-to-content">{{ msg.reply_to.content || '[文件/图片]' }}</span>
                  </div>
                  <div v-if="msg.is_recalled" class="message-bubble recalled">
                    {{ msg.sender.username }} 撤回了一条消息
                  </div>
                  <div v-else-if="msg.message_type === 'image'" class="message-bubble image-message">
                    <div v-if="!imageLoaded[msg.id]" class="image-loading-placeholder">
                      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                    </div>
                    <img
                      v-show="imageLoaded[msg.id]"
                      :src="msg.file_url"
                      alt="图片"
                      @click="openImagePreview(msg.file_url)"
                      @load="onImageLoad(msg.id)"
                      @error="onImageError(msg.id)"
                    />
                    <div v-if="imageError[msg.id]" class="image-error-placeholder">
                      <el-icon :size="24"><PictureFilled /></el-icon>
                      <span>图片加载失败</span>
                    </div>
                  </div>
                  <div v-else-if="msg.message_type === 'file'" class="message-bubble file-message">
                    <el-icon :size="24"><Document /></el-icon>
                    <div class="file-info">
                      <span class="file-name">{{ msg.file_name }}</span>
                      <span class="file-size">{{ formatFileSize(msg.file_size) }}</span>
                    </div>
                    <el-button size="small" @click="downloadFile(msg.file_url, msg.file_name)">下载</el-button>
                  </div>
                  <div v-else class="message-bubble">
                    <span v-html="parseMentions(msg.content)"></span>
                    <span v-if="msg.edited_at" class="edited-mark">(已编辑)</span>
                  </div>
                  <div v-if="msg.sender.id === userStore.user?.id && !msg.is_recalled" class="message-status">
                    <el-icon v-if="msg._sending" class="is-loading"><Loading /></el-icon>
                    <el-icon v-else-if="msg._error" class="error-icon" @click="retryMessage(msg)"><WarningFilled /></el-icon>
                    <template v-else>
                      <el-icon v-if="msg.is_read" class="read-icon"><Check /></el-icon>
                      <span>{{ msg.is_read ? '已读' : '未读' }}</span>
                    </template>
                  </div>
                </div>
              </template>
            </div>
          </transition-group>
          <div v-if="currentMessages.length === 0" class="empty-messages">
            <el-icon :size="64"><ChatDotRound /></el-icon>
            <p>发送消息开始聊天</p>
          </div>
        </div>

        <div class="message-input-area">
          <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
            <el-progress :percentage="uploadProgress" :stroke-width="3" />
          </div>
          <div v-if="replyingTo" class="reply-bar">
            <div class="reply-bar-content">
              <span class="reply-label">回复 {{ replyingTo.sender.username }}:</span>
              <span class="reply-text">{{ replyingTo.content || '[文件/图片]' }}</span>
            </div>
            <el-button circle size="small" @click="cancelReply">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div class="input-actions">
            <el-upload
              :show-file-list="false"
              :before-upload="handleImageUpload"
              accept="image/*"
            >
              <el-button circle title="发送图片">
                <el-icon><Picture /></el-icon>
              </el-button>
            </el-upload>
            <el-upload
              :show-file-list="false"
              :before-upload="handleFileUpload"
            >
              <el-button circle title="发送文件">
                <el-icon><Folder /></el-icon>
              </el-button>
            </el-upload>
            <el-popover
              :visible="showEmojiPicker"
              placement="top"
              :width="340"
              trigger="click"
            >
              <template #reference>
                <el-button circle title="表情" @click="showEmojiPicker = !showEmojiPicker">
                  <span class="emoji-btn-icon">😊</span>
                </el-button>
              </template>
              <div class="emoji-picker">
                <span
                  v-for="emoji in emojis"
                  :key="emoji"
                  class="emoji-item"
                  @click="insertEmoji(emoji)"
                >
                  {{ emoji }}
                </span>
              </div>
            </el-popover>
          </div>
          <div class="input-wrapper" style="position: relative;">
            <el-input
              ref="inputRef"
              type="textarea"
              v-model="inputMessage"
              placeholder="输入消息..."
              :autosize="{ minRows: 1, maxRows: 6 }"
              @keydown="handleInputKeydown"
              @input="handleTyping"
              :disabled="!chatStore.currentConversation"
              class="message-input"
              resize="none"
            />
            <div v-if="showMentionList && currentConv?.type === 'group'" class="mention-list">
              <div
                v-for="member in filteredMembers"
                :key="member.user.id"
                class="mention-item"
                @click="selectMention(member)"
              >
                <el-avatar :size="24" :src="member.user.avatar">
                  {{ member.user.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <span>{{ member.user.username }}</span>
              </div>
            </div>
            <el-button
              type="primary"
              circle
              class="send-btn"
              @click="sendMessage"
              :disabled="!inputMessage.trim()"
            >
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
        </template>
      </template>

      <template v-else>
        <div class="welcome-screen">
          <el-button v-if="isMobile" circle class="welcome-hamburger-btn" @click="sidebarCollapsed = false">
            <el-icon><Menu /></el-icon>
          </el-button>
          <div class="welcome-content">
            <div class="welcome-icon">
              <el-icon :size="80"><ChatDotRound /></el-icon>
            </div>
            <h2>欢迎使用 ChatApp</h2>
            <p>选择一个会话开始聊天，或添加好友开始新的对话</p>
            <div class="welcome-actions">
              <el-button type="primary" @click="showAddFriend = true">
                <el-icon><Plus /></el-icon>添加好友
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <el-dialog v-model="showAddFriend" title="添加好友" width="400px" class="modern-dialog">
      <el-input
        v-model="userSearchQuery"
        placeholder="搜索用户..."
        :prefix-icon="Search"
        @input="searchUsers"
        style="margin-bottom: 16px"
      />
      <div class="user-search-results">
        <div v-for="user in searchedUsers" :key="user.id" class="user-search-item">
          <el-avatar :size="36">{{ user.username.charAt(0).toUpperCase() }}</el-avatar>
          <span class="user-name">{{ user.username }}</span>
          <el-button type="primary" size="small" @click="sendFriendRequest(user.id)">添加</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAddFriend = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateGroup" title="创建群聊" width="450px" class="modern-dialog">
      <el-form label-width="80px" class="group-form">
        <el-form-item label="群名称">
          <el-input v-model="groupName" placeholder="请输入群名称" />
        </el-form-item>
        <el-form-item label="成员">
          <el-select v-model="groupMembers" multiple placeholder="选择成员" class="member-select">
            <el-option
              v-for="friendship in chatStore.friends"
              :key="friendship.friend.id"
              :label="friendship.friend.username"
              :value="friendship.friend.id"
            >
              <div class="user-option">
                <el-avatar :size="28">{{ friendship.friend.username.charAt(0).toUpperCase() }}</el-avatar>
                <span>{{ friendship.friend.username }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateGroup = false">取消</el-button>
        <el-button type="primary" @click="handleCreateGroup">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSettings" title="设置" width="400px" class="modern-dialog">
      <div class="settings-content">
        <div class="setting-item">
          <span>深色模式</span>
          <el-switch v-model="isDarkMode" @change="toggleDarkMode" />
        </div>
        <div class="setting-item">
          <span>消息通知</span>
          <el-switch v-model="notificationEnabled" @change="toggleNotification" />
        </div>
        <el-divider />
        <el-button type="primary" plain @click="showDeviceManager = true" style="width: 100%; margin-bottom: 12px;">
          <el-icon><Monitor /></el-icon> 设备管理
        </el-button>
        <el-button type="danger" plain @click="showChangePassword = true">修改密码</el-button>
        <el-button type="danger" @click="handleDeleteAccount">注销账号</el-button>
      </div>
    </el-dialog>

    <el-dialog v-model="showDeviceManager" title="设备管理" width="500px" class="modern-dialog">
      <div class="device-manager">
        <div class="device-header">
          <span>已登录设备</span>
          <el-button type="danger" size="small" @click="logoutAllOther" :disabled="deviceList.length <= 1">
            踢出所有其他设备
          </el-button>
        </div>
        <div class="device-list">
          <div v-for="device in deviceList" :key="device.id" class="device-item" :class="{ current: device.is_current }">
            <div class="device-icon">
              <el-icon :size="24"><Monitor /></el-icon>
            </div>
            <div class="device-info">
              <div class="device-name">
                {{ device.device_name || '未知设备' }}
                <el-tag v-if="device.is_current" type="success" size="small">当前设备</el-tag>
              </div>
              <div class="device-meta">
                <span>{{ device.ip_address }}</span>
                <span>登录于 {{ formatTime(device.created_at) }}</span>
              </div>
            </div>
            <el-button
              v-if="!device.is_current"
              type="danger"
              size="small"
              @click="kickDevice(device.id)"
            >
              踢出
            </el-button>
          </div>
          <div v-if="deviceList.length === 0" class="empty-devices">
            <el-icon :size="48"><Monitor /></el-icon>
            <p>暂无已登录设备</p>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showChangePassword" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="80px">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSearchMessages" title="搜索消息" width="500px">
      <el-input v-model="messageSearchQuery" placeholder="输入关键词搜索..." @input="searchMessages" />
      <div class="search-results">
        <div v-for="msg in searchedMessages" :key="msg.id" class="search-result-item" @click="jumpToMessage(msg)">
          <div class="search-result-sender">{{ msg.sender.username }}</div>
          <div class="search-result-content" v-html="highlightText(msg.content, messageSearchQuery)"></div>
          <div class="search-result-time">{{ formatMessageTime(msg.created_at) }}</div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showForwardDialog" title="转发消息" width="400px" class="modern-dialog">
      <div class="forward-list">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          :class="['forward-item', { selected: selectedForwardConv === conv.id }]"
          @click="selectedForwardConv = conv.id"
        >
          <el-avatar :size="36">{{ getConversationAvatar(conv) }}</el-avatar>
          <span class="forward-name">{{ getConversationName(conv) }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="showForwardDialog = false">取消</el-button>
        <el-button type="primary" @click="handleForward" :disabled="!selectedForwardConv">转发</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showFavoritesDialog" title="我的收藏" width="500px" class="modern-dialog">
      <div class="favorites-list">
        <div v-for="msg in favoriteMessages" :key="msg.id" class="favorite-item">
          <div class="favorite-header">
            <span class="favorite-sender">{{ msg.sender.username }}</span>
            <span class="favorite-time">{{ formatMessageTime(msg.created_at) }}</span>
          </div>
          <div class="favorite-content">{{ msg.content }}</div>
        </div>
        <div v-if="favoriteMessages.length === 0" class="empty-state">
          <el-icon :size="48"><Star /></el-icon>
          <p>暂无收藏</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showBlacklistDialog" title="黑名单" width="500px" class="modern-dialog">
      <div class="blacklist-container">
        <div v-for="item in blacklist" :key="item.id" class="blacklist-item">
          <div class="blacklist-user">
            <el-avatar :size="40">{{ item.blocked_user.username.charAt(0).toUpperCase() }}</el-avatar>
            <div class="blacklist-info">
              <span class="blacklist-name">{{ item.blocked_user.username }}</span>
              <span class="blacklist-time">拉黑时间: {{ formatMessageTime(item.created_at) }}</span>
            </div>
          </div>
          <el-button type="primary" size="small" @click="unblockUser(item.blocked_user.id)">取消拉黑</el-button>
        </div>
        <div v-if="blacklist.length === 0" class="empty-state">
          <el-icon :size="48"><Hide /></el-icon>
          <p>黑名单为空</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showRemarkDialog" title="设置备注" width="400px">
      <el-input v-model="remarkInput" placeholder="请输入备注名" />
      <template #footer>
        <el-button @click="showRemarkDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSetRemark">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editingMessage" title="编辑消息" width="400px" class="modern-dialog" @close="cancelEditMessage">
      <el-input
        v-model="editingMessageContent"
        type="textarea"
        :rows="3"
        placeholder="输入新内容..."
      />
      <template #footer>
        <el-button @click="cancelEditMessage">取消</el-button>
        <el-button type="primary" @click="saveEditMessage">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showGroupSettings" title="群设置" width="500px" class="modern-dialog">
      <div v-if="currentConv" class="group-settings">
        <div class="group-info">
          <div class="group-avatar-section">
            <el-upload
              v-if="isGroupOwner || isGroupAdmin"
              :show-file-list="false"
              :before-upload="handleGroupAvatarUpload"
              accept="image/*"
            >
              <el-avatar :size="80" :src="currentConv.avatar" class="group-avatar">
                {{ currentConv.name?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div v-if="isGroupOwner || isGroupAdmin" class="avatar-upload-hint">点击更换</div>
            </el-upload>
            <el-avatar v-else :size="80" :src="currentConv.avatar" class="group-avatar">
              {{ currentConv.name?.charAt(0)?.toUpperCase() }}
            </el-avatar>
          </div>
          <div class="group-name-section">
            <div v-if="!isEditingGroupName" class="group-name-display">
              <span class="group-name">{{ currentConv.name }}</span>
              <el-button v-if="isGroupOwner || isGroupAdmin" size="small" circle @click="startEditGroupName">
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
            <div v-else class="group-name-edit">
              <el-input v-model="editingGroupName" size="small" style="width: 200px" />
              <el-button size="small" type="primary" @click="saveGroupName">保存</el-button>
              <el-button size="small" @click="isEditingGroupName = false">取消</el-button>
            </div>
          </div>
          <div class="group-invite-code">
            <div class="invite-code-header">
              <el-icon><Key /></el-icon>
              <span>群邀请码</span>
            </div>
            <div class="invite-code-content">
              <span class="invite-code-value">{{ currentConv.invite_code || '未生成' }}</span>
              <el-button v-if="isGroupOwner || isGroupAdmin" size="small" type="primary" @click="copyInviteCode">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
            </div>
            <div class="invite-code-hint" v-if="isGroupOwner || isGroupAdmin">
              分享邀请码给好友，让他们加入群聊
            </div>
          </div>
        </div>
        <el-divider />
        <div class="group-announcement" v-if="currentConv.announcement">
          <h4>群公告</h4>
          <p>{{ currentConv.announcement }}</p>
        </div>
        <div v-if="isGroupOwner || isGroupAdmin" class="announcement-edit">
          <el-input
            v-model="announcementInput"
            type="textarea"
            :rows="2"
            placeholder="设置群公告..."
          />
          <el-button size="small" type="primary" @click="handleSetAnnouncement">保存</el-button>
        </div>
        <el-divider />
        <div class="group-members">
          <h4>群成员 ({{ currentConv.members?.length || 0 }})</h4>
          <div class="my-nickname" v-if="currentConv.type === 'group'">
            <span>我的群昵称：</span>
            <el-input v-model="myNickname" size="small" style="width: 150px" placeholder="设置昵称" />
            <el-button size="small" type="primary" @click="saveMyNickname">保存</el-button>
          </div>
          <div class="member-grid">
            <div v-for="member in currentConv.members" :key="member.user.id" class="member-card">
              <el-avatar :size="40" :src="member.user.avatar" @click="showUserProfile(member.user)" style="cursor:pointer">
                {{ member.user.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="member-info">
                <div class="member-name-row">
                  <span class="member-name">{{ member.user.username }}</span>
                  <span v-if="currentConv.owner?.id === member.user.id" class="member-role owner">群主</span>
                  <span v-else-if="member.role === 'admin'" class="member-role admin">管理员</span>
                </div>
              </div>
              <div class="member-actions">
                <el-dropdown v-if="isGroupOwner && currentConv.owner?.id !== member.user.id" trigger="click" @command="(cmd) => handleMemberAction(cmd, member)">
                  <el-button size="small" circle>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="member.role === 'admin' ? 'removeAdmin' : 'setAdmin'">
                        {{ member.role === 'admin' ? '取消管理员' : '设为管理员' }}
                      </el-dropdown-item>
                      <el-dropdown-item :command="member.is_muted ? 'unmute' : 'mute'">
                        {{ member.is_muted ? '解除禁言' : '禁言' }}
                      </el-dropdown-item>
                      <el-dropdown-item command="transferOwner" divided>
                        转让群主
                      </el-dropdown-item>
                      <el-dropdown-item command="kick" divided>
                        移除成员
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-dropdown v-else-if="isGroupAdmin && currentConv.owner?.id !== member.user.id && member.role !== 'admin'" trigger="click" @command="(cmd) => handleMemberAction(cmd, member)">
                  <el-button size="small" circle>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="member.is_muted ? 'unmute' : 'mute'">
                        {{ member.is_muted ? '解除禁言' : '禁言' }}
                      </el-dropdown-item>
                      <el-dropdown-item command="kick" divided>
                        移除成员
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
        <el-divider />
        <div class="transfer-records" v-if="transferRecords.length > 0">
          <h4>转让记录</h4>
          <div class="records-list">
            <div v-for="record in transferRecords" :key="record.id" class="record-item">
              <span class="record-text">{{ record.old_owner.username }} → {{ record.new_owner.username }}</span>
              <span class="record-time">{{ formatMessageTime(record.transferred_at) }}</span>
            </div>
          </div>
        </div>
        <el-divider />
        <div class="group-bottom-actions">
          <el-button
            v-if="!isGroupOwner"
            type="warning"
            @click="leaveGroup"
          >
            退出群聊
          </el-button>
          <el-button
            v-if="isGroupOwner"
            type="danger"
            @click="dissolveGroup"
          >
            解散群聊
          </el-button>
        </div>
      </div>
    </el-dialog>

    <teleport to="body">
      <div v-if="contextMenu.visible" class="context-menu" :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }">
        <div v-if="contextMenu.message?.sender.id === userStore.user?.id && !contextMenu.message?.is_recalled" class="context-menu-item" @click="recallMessage">
          撤回消息
        </div>
        <div v-if="canEditMessage" class="context-menu-item" @click="editMessage">
          编辑消息
        </div>
        <div class="context-menu-item" @click="replyMessage">
          回复
        </div>
        <div class="context-menu-item" @click="forwardMessage">
          转发
        </div>
        <div class="context-menu-item" @click="favoriteMessage">
          收藏
        </div>
        <div class="context-menu-item" @click="copyMessage">
          复制内容
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="convContextMenu.visible" class="context-menu" :style="{ top: convContextMenu.y + 'px', left: convContextMenu.x + 'px' }">
        <div class="context-menu-item" @click="togglePinConversation">
          {{ convContextMenu.conversation?.is_pinned ? '取消置顶' : '置顶' }}
        </div>
        <div class="context-menu-item" @click="toggleMuteConversation">
          {{ convContextMenu.conversation?.is_muted ? '取消免打扰' : '免打扰' }}
        </div>
        <div class="context-menu-item danger" @click="deleteConversation">
          删除会话
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="friendContextMenu.visible" class="context-menu" :style="{ top: friendContextMenu.y + 'px', left: friendContextMenu.x + 'px' }">
        <div class="context-menu-item" @click="openRemarkDialog">
          设置备注
        </div>
        <div class="context-menu-item" @click="openTagsDialog">
          设置标签
        </div>
        <div class="context-menu-item has-submenu">
          移动到分组
          <div class="context-submenu">
            <div class="context-menu-item" @click="moveToGroup(null)">
              我的好友
            </div>
            <div v-for="group in friendGroupsList" :key="group.id" class="context-menu-item" @click="moveToGroup(group.id)">
              {{ group.name }}
            </div>
          </div>
        </div>
        <div class="context-menu-item danger" @click="deleteFriend">
          删除好友
        </div>
        <div class="context-menu-item danger" @click="blockFriend">
          拉黑
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="imagePreviewUrl" class="image-preview-overlay" @click="closeImagePreview">
        <img :src="imagePreviewUrl" class="image-preview-img" @click.stop />
        <el-button class="close-btn" circle @click="closeImagePreview">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </teleport>

    <el-dialog v-model="showProfileEdit" title="个人资料" width="420px" class="modern-dialog">
      <div class="profile-edit-content">
        <div class="profile-avatar-section">
          <el-upload
            :show-file-list="false"
            :before-upload="handleProfileAvatarUpload"
            accept="image/*"
          >
            <el-avatar :size="80" :src="profileEditData.avatar || userStore.user?.avatar || undefined" class="profile-edit-avatar">
              {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div class="avatar-upload-hint">点击更换</div>
          </el-upload>
        </div>
        <el-form label-width="80px" class="profile-form">
          <el-form-item label="用户名">
            <el-input :model-value="userStore.user?.username" disabled />
          </el-form-item>
          <el-form-item label="个性签名">
            <el-input v-model="profileEditData.signature" type="textarea" :rows="2" placeholder="写点什么..." />
          </el-form-item>
          <el-form-item label="在线状态">
            <el-select v-model="profileEditData.status" placeholder="选择状态">
              <el-option label="🟢 在线" value="online" />
              <el-option label="🔴 忙碌" value="busy" />
              <el-option label="🟡 离开" value="away" />
              <el-option label="⚫ 隐身" value="invisible" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showProfileEdit = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showUserProfileDialog" title="用户资料" width="400px" class="modern-dialog">
      <div v-if="viewingUser" class="user-profile-card">
        <div class="profile-card-avatar">
          <el-avatar :size="72" :src="viewingUser.avatar || undefined">
            {{ viewingUser.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <span :class="['status-dot-lg', viewingUser.is_online ? 'online' : 'offline']"></span>
        </div>
        <div class="profile-card-info">
          <h3>{{ viewingUser.username }}</h3>
          <p class="profile-signature">{{ viewingUser.signature || '这个人很懒，什么都没写' }}</p>
          <span class="profile-status-text">{{ viewingUser.is_online ? '在线' : '离线' }}</span>
        </div>
        <div class="profile-card-actions">
          <el-button type="primary" @click="startChat(viewingUser.id); showUserProfileDialog = false">
            <el-icon><ChatDotRound /></el-icon>发消息
          </el-button>
          <el-button @click="openRemarkFromProfile(viewingUser.id)">
            设置备注
          </el-button>
          <el-button type="danger" plain @click="blockUserFromProfile(viewingUser.id)">
            拉黑
          </el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showJoinGroup" title="加入群聊" width="400px" class="modern-dialog">
      <el-input v-model="inviteCodeInput" placeholder="请输入邀请码" />
      <template #footer>
        <el-button @click="showJoinGroup = false">取消</el-button>
        <el-button type="primary" @click="handleJoinGroup" :disabled="!inviteCodeInput.trim()">加入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateFriendGroup" title="创建分组" width="400px" class="modern-dialog">
      <el-input v-model="newFriendGroupName" placeholder="请输入分组名称" />
      <template #footer>
        <el-button @click="showCreateFriendGroup = false">取消</el-button>
        <el-button type="primary" @click="handleCreateFriendGroup" :disabled="!newFriendGroupName.trim()">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSetTags" title="设置好友标签" width="400px" class="modern-dialog">
      <el-input v-model="friendTagsInput" placeholder="输入标签，用逗号分隔" />
      <div class="tags-preview" v-if="friendTagsInput">
        <el-tag v-for="tag in friendTagsInput.split(',').filter(t => t.trim())" :key="tag" class="tag-item">
          {{ tag.trim() }}
        </el-tag>
      </div>
      <template #footer>
        <el-button @click="showSetTags = false">取消</el-button>
        <el-button type="primary" @click="saveFriendTags">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch, onUnmounted } from "vue";
import { useUserStore } from "../stores/user";
import { useChatStore } from "../stores/chat";
import { userApi, chatApi } from "../api/modules";
import { wsManager } from "../utils/websocket";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search, Key, CopyDocument, Edit, Menu, Monitor } from "@element-plus/icons-vue";

const router = useRouter();
const userStore = useUserStore();
const chatStore = useChatStore();

const activeTab = ref("conversations");
const inputMessage = ref("");
const messageListRef = ref(null);
const inputRef = ref(null);
const showAddFriend = ref(false);
const showCreateGroup = ref(false);
const showSettings = ref(false);
const showChangePassword = ref(false);
const showSearchMessages = ref(false);
const showForwardDialog = ref(false);
const showDeviceManager = ref(false);
const deviceList = ref([]);
const showFavoritesDialog = ref(false);
const showBlacklistDialog = ref(false);
const showRemarkDialog = ref(false);
const showGroupSettings = ref(false);
const showEmojiPicker = ref(false);
const selectedUserId = ref(null);
const allUsers = ref([]);
const groupName = ref("");
const groupMembers = ref([]);
const isEditingGroupName = ref(false);
const editingGroupName = ref("");
const searchQuery = ref("");
const userSearchQuery = ref("");
const searchedUsers = ref([]);
const messageSearchQuery = ref("");
const searchedMessages = ref([]);
const isDarkMode = ref(localStorage.getItem("darkMode") === "true");
const notificationEnabled = ref(Notification.permission === "granted");
const passwordForm = reactive({ oldPassword: "", newPassword: "" });
const passwordFormRef = ref(null);
const passwordRules = {
  oldPassword: [{ required: true, message: "请输入旧密码", trigger: "blur" }],
  newPassword: [{ required: true, message: "请输入新密码", trigger: "blur" }, { min: 6, message: "密码至少6位", trigger: "blur" }],
};
const contextMenu = reactive({ visible: false, x: 0, y: 0, message: null });
const convContextMenu = reactive({ visible: false, x: 0, y: 0, conversation: null });
const friendContextMenu = reactive({ visible: false, x: 0, y: 0, friendship: null });
const typingTimeout = ref(null);
const replyingTo = ref(null);
const selectedForwardConv = ref(null);
const favoriteMessages = ref([]);
const blacklist = ref([]);
const remarkInput = ref("");
const announcementInput = ref("");
const imagePreviewUrl = ref(null);
const loadingMore = ref(false);
const hasMoreMessages = ref(true);
const mentionQuery = ref("");
const showMentionList = ref(false);
const showProfileEdit = ref(false);
const showUserProfileDialog = ref(false);
const showJoinGroup = ref(false);
const showCreateFriendGroup = ref(false);
const viewingUser = ref(null);
const inviteCodeInput = ref("");
const newFriendGroupName = ref("");
const showOnlineOnly = ref(false);
const friendGroupsList = ref([]);
const showSetTags = ref(false);
const friendTagsInput = ref("");
const settingTagsFriendId = ref(null);
const myNickname = ref("");
const transferRecords = ref([]);
const expandedGroups = reactive({ default: true });
const profileEditData = reactive({
  signature: "",
  status: "online",
  avatar: "",
});
const initialLoading = ref(true);
const messagesLoading = ref(false);
const messageDrafts = reactive({});
const sidebarCollapsed = ref(false);
const isMobile = ref(window.innerWidth <= 768);
const isDragging = ref(false);
const uploadProgress = ref(0);
const imageLoaded = reactive({});
const imageError = reactive({});

const emojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😊',
  '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '🥲', '😋',
  '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐',
  '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '😮', '🤯',
  '😱', '🥵', '🥶', '😰', '😥', '😢', '😭', '😤', '😡', '🤬',
  '👍', '👎', '👏', '🙌', '🤝', '❤️', '💔', '💯', '🎉', '🔥'
];

const pendingRequestsCount = computed(() => chatStore.friendRequests.filter(r => r.status === "pending").length);

const pendingRequests = computed(() => chatStore.friendRequests.filter(r => r.status === "pending"));

const statusText = computed(() => {
  const map = { online: "在线", busy: "忙碌", away: "离开", invisible: "隐身" };
  return map[userStore.user?.status || "online"] || "在线";
});

const searchConvResults = computed(() => {
  if (!searchQuery.value) return [];
  return chatStore.conversations.filter((conv) =>
    getConversationName(conv).toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const filteredConversations = computed(() => {
  if (!searchQuery.value) return chatStore.conversations;
  return chatStore.conversations.filter((conv) =>
    getConversationName(conv).toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const searchFriendResults = computed(() => {
  if (!searchQuery.value) return [];
  return chatStore.friends.filter((f) =>
    (f.remark || f.friend.username).toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const onlineFriendCount = computed(() => chatStore.friends.filter(f => f.friend.is_online).length);

const defaultGroupFriends = computed(() => {
  let friends = chatStore.friends.filter(f => !f.group);
  if (showOnlineOnly.value) friends = friends.filter(f => f.friend.is_online);
  return friends;
});

const filteredFriends = computed(() => {
  let friends = chatStore.friends;
  if (showOnlineOnly.value) friends = friends.filter(f => f.friend.is_online);
  if (!searchQuery.value) return friends;
  return friends.filter((f) =>
    (f.remark || f.friend.username).toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const currentMessages = computed(() => {
  if (!chatStore.currentConversation) return [];
  return chatStore.messages[chatStore.currentConversation] || [];
});

const currentConv = computed(() => {
  return chatStore.conversations.find((c) => c.id === chatStore.currentConversation);
});

const currentConvName = computed(() => {
  const conv = currentConv.value;
  if (!conv) return "";
  return getConversationName(conv);
});

const currentConvAvatar = computed(() => {
  const conv = currentConv.value;
  if (!conv) return "";
  return getConversationAvatar(conv);
});

const currentConvStatus = computed(() => {
  const conv = currentConv.value;
  if (!conv) return "";
  if (conv.type === "group") return `${conv.members?.length || 0} 人`;
  const other = getOtherMember(conv);
  return other?.is_online ? "在线" : "离线";
});

const typingUsersText = computed(() => {
  const typing = chatStore.typingUsers[chatStore.currentConversation];
  if (!typing || Object.keys(typing).length === 0) return "";
  const names = Object.values(typing);
  if (names.length === 1) return `${names[0]} 正在输入...`;
  return `${names.slice(0, 2).join("、")} 正在输入...`;
});

const isGroupOwner = computed(() => {
  const conv = currentConv.value;
  if (!conv || conv.type !== "group") return false;
  return conv.owner?.id === userStore.user?.id;
});

const isGroupAdmin = computed(() => {
  const conv = currentConv.value;
  if (!conv || conv.type !== "group") return false;
  const member = conv.members?.find(m => m.user.id === userStore.user?.id);
  return member?.role === "admin";
});

const filteredMembers = computed(() => {
  const conv = currentConv.value;
  if (!conv || conv.type !== "group") return [];
  if (!mentionQuery.value) return conv.members || [];
  return (conv.members || []).filter(m =>
    m.user.username.toLowerCase().includes(mentionQuery.value.toLowerCase())
  );
});

function getConversationName(conv) {
  if (conv.type === "group") return conv.name || "群聊";
  const other = getOtherMember(conv);
  return other?.username || "聊天";
}

function getConversationAvatar(conv) {
  if (conv.type === "group") return conv.name?.charAt(0)?.toUpperCase() || "G";
  const other = getOtherMember(conv);
  return other?.username?.charAt(0)?.toUpperCase() || "?";
}

function getOtherMember(conv) {
  if (!conv.members) return null;
  return conv.members.find((m) => m.user.id !== userStore.user?.id)?.user;
}

function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

function formatMessageTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function getMemberDisplayName(sender) {
  if (!currentConv.value || currentConv.value.type !== "group") {
    return sender.username;
  }
  const member = currentConv.value.members?.find(m => m.user.id === sender.id);
  return member?.nickname || sender.username;
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function parseMentions(content) {
  if (!content) return "";
  return content.replace(/@(\S+)/g, '<span class="mention">@$1</span>');
}

function isConsecutiveMessage(messages, index) {
  if (index === 0) return false;
  const prev = messages[index - 1];
  const curr = messages[index];
  if (prev.sender.id !== curr.sender.id) return false;
  const prevTime = new Date(prev.created_at).getTime();
  const currTime = new Date(curr.created_at).getTime();
  return (currTime - prevTime) < 5 * 60 * 1000;
}

function highlightText(text, query) {
  if (!text || !query) return text || "";
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

function onImageLoad(msgId) {
  imageLoaded[msgId] = true;
}

function onImageError(msgId) {
  imageError[msgId] = true;
  imageLoaded[msgId] = false;
}

function playNotificationSound() {
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

async function handlePaste(e) {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const file = item.getAsFile();
      if (file) await uploadAndSendFile(file);
      return;
    }
  }
}

async function handleDrop(e) {
  isDragging.value = false;
  const files = e.dataTransfer?.files;
  if (!files || files.length === 0) return;
  for (const file of files) {
    await uploadAndSendFile(file);
  }
}

async function uploadAndSendFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  uploadProgress.value = 10;
  try {
    const res = await chatApi.uploadFile(formData);
    uploadProgress.value = 100;
    const type = file.type.startsWith('image/') ? 'image' : 'file';
    wsManager.sendMessage(chatStore.currentConversation, "", type, res.data.url, res.data.name, res.data.size);
  } catch (e) {
    ElMessage.error("文件上传失败");
  } finally {
    setTimeout(() => { uploadProgress.value = 0; }, 500);
  }
}

async function selectConversation(conv) {
  if (chatStore.currentConversation && inputMessage.value) {
    messageDrafts[chatStore.currentConversation] = inputMessage.value;
  } else if (chatStore.currentConversation) {
    delete messageDrafts[chatStore.currentConversation];
  }
  hasMoreMessages.value = true;
  messagesLoading.value = true;
  try {
    await chatStore.fetchMessages(conv.id);
  } finally {
    messagesLoading.value = false;
  }
  inputMessage.value = messageDrafts[conv.id] || '';
  wsManager.markRead(conv.id);
  chatStore.clearUnreadCount(conv.id);
  if (isMobile.value) {
    sidebarCollapsed.value = true;
  }
  await nextTick();
  scrollToBottom();
}

async function sendMessage() {
  if (!inputMessage.value.trim() || !chatStore.currentConversation) return;

  const content = inputMessage.value.trim();
  const replyToId = replyingTo.value?.id || null;

  const mentionedUserIds = [];
  if (currentConv.value?.type === "group") {
    const mentions = content.match(/@(\S+)/g);
    if (mentions) {
      mentions.forEach(mention => {
        const username = mention.slice(1);
        const member = currentConv.value.members?.find(m => m.user.username === username);
        if (member && !mentionedUserIds.includes(member.user.id)) {
          mentionedUserIds.push(member.user.id);
        }
      });
    }
  }

  const clientMessageId = wsManager.generateMessageId();
  const tempId = `temp_${Date.now()}`;
  const tempMsg = {
    id: tempId,
    client_message_id: clientMessageId,
    content,
    sender: userStore.user,
    created_at: new Date().toISOString(),
    message_type: "text",
    is_read: false,
    _sending: true,
    _error: false,
    reply_to: replyingTo.value,
  };
  chatStore.addMessage(chatStore.currentConversation, tempMsg);

  inputMessage.value = "";
  delete messageDrafts[chatStore.currentConversation];
  replyingTo.value = null;
  showMentionList.value = false;
  wsManager.sendTyping(chatStore.currentConversation, false);
  await nextTick();
  scrollToBottom();

  try {
    await wsManager.sendMessageWithId(
      chatStore.currentConversation,
      content,
      clientMessageId,
      "text",
      "",
      "",
      0,
      replyToId,
      mentionedUserIds
    );
  } catch (error) {
    const msgs = chatStore.messages[chatStore.currentConversation];
    const idx = msgs.findIndex(m => m.client_message_id === clientMessageId);
    if (idx !== -1) {
      msgs[idx]._sending = false;
      msgs[idx]._error = true;
    }
    if (error?.error === 'blocked') {
      ElMessage.error(error.message || "对方已将您加入黑名单，无法发送消息");
    } else {
      ElMessage.error("消息发送失败");
    }
  }
}

function retryMessage(msg) {
  const msgs = chatStore.messages[chatStore.currentConversation];
  const idx = msgs.findIndex(m => m.id === msg.id);
  if (idx !== -1) {
    msgs.splice(idx, 1);
    inputMessage.value = msg.content;
    if (msg.reply_to) {
      replyingTo.value = msg.reply_to;
    }
  }
}

function handleTyping() {
  if (!chatStore.currentConversation) return;

  const conv = currentConv.value;
  if (conv?.type === "group") {
    const lastAtIndex = inputMessage.value.lastIndexOf("@");
    if (lastAtIndex !== -1) {
      const textAfterAt = inputMessage.value.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(" ")) {
        mentionQuery.value = textAfterAt;
        showMentionList.value = true;
      } else {
        showMentionList.value = false;
      }
    } else {
      showMentionList.value = false;
    }
  }

  if (typingTimeout.value) clearTimeout(typingTimeout.value);
  wsManager.sendTyping(chatStore.currentConversation, true);
  typingTimeout.value = setTimeout(() => {
    wsManager.sendTyping(chatStore.currentConversation, false);
  }, 2000);
}

function handleInputKeydown(e) {
  if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function selectMention(member) {
  const lastAtIndex = inputMessage.value.lastIndexOf("@");
  inputMessage.value = inputMessage.value.slice(0, lastAtIndex + 1) + member.user.username + " ";
  showMentionList.value = false;
  nextTick(() => {
    inputRef.value?.focus();
  });
}

function cancelReply() {
  replyingTo.value = null;
}

function insertEmoji(emoji) {
  inputMessage.value += emoji;
  showEmojiPicker.value = false;
}

async function startChat(friendId) {
  try {
    const conv = await chatStore.startPrivateChat(friendId);
    await chatStore.fetchMessages(conv.id);
    activeTab.value = "conversations";
    await nextTick();
    scrollToBottom();
  } catch (error) {
    ElMessage.error("创建会话失败");
  }
}

async function handleCreateGroup() {
  if (!groupName.value.trim()) {
    ElMessage.warning("请输入群名称");
    return;
  }
  if (groupMembers.value.length === 0) {
    ElMessage.warning("请选择群成员");
    return;
  }
  try {
    await chatStore.createGroup(groupName.value.trim(), groupMembers.value);
    ElMessage.success("创建群聊成功");
    showCreateGroup.value = false;
    groupName.value = "";
    groupMembers.value = [];
  } catch (error) {
    ElMessage.error("创建群聊失败");
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
}

function handleCommand(command) {
  if (command === "addFriend") {
    showAddFriend.value = true;
  } else if (command === "createGroup") {
    showCreateGroup.value = true;
  } else if (command === "joinGroup") {
    inviteCodeInput.value = "";
    showJoinGroup.value = true;
  } else if (command === "toggleDarkMode") {
    toggleDarkMode();
  } else if (command === "logout") {
    wsManager.disconnect();
    userStore.logout();
    router.push("/login");
  } else if (command === "showFavorites") {
    loadFavorites();
    showFavoritesDialog.value = true;
  } else if (command === "showBlacklist") {
    loadBlacklist();
    showBlacklistDialog.value = true;
  }
}

async function searchUsers() {
  if (!userSearchQuery.value.trim()) {
    searchedUsers.value = [];
    return;
  }
  try {
    const res = await userApi.searchUsers(userSearchQuery.value);
    searchedUsers.value = res.data.filter(u => u.id !== userStore.user?.id);
  } catch (e) {
    console.error(e);
  }
}

async function sendFriendRequest(userId) {
  try {
    await chatApi.sendFriendRequest(userId);
    ElMessage.success("好友申请已发送");
  } catch (e) {
    ElMessage.error("发送失败");
  }
}

async function searchMessages() {
  if (!messageSearchQuery.value.trim()) {
    searchedMessages.value = [];
    return;
  }
  try {
    const res = await chatApi.searchMessages(messageSearchQuery.value);
    searchedMessages.value = res.data;
  } catch (e) {
    console.error(e);
  }
}

function jumpToMessage(msg) {
  showSearchMessages.value = false;
  chatStore.currentConversation = msg.conversation;
}

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem("darkMode", isDarkMode.value);
}

async function toggleNotification() {
  if (notificationEnabled.value) {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      notificationEnabled.value = false;
      ElMessage.warning("请允许浏览器通知");
    }
  }
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  try {
    await userApi.changePassword(passwordForm);
    ElMessage.success("密码修改成功");
    showChangePassword.value = false;
    passwordForm.oldPassword = "";
    passwordForm.newPassword = "";
  } catch (e) {
    ElMessage.error("密码修改失败");
  }
}

async function handleDeleteAccount() {
  try {
    await ElMessageBox.confirm("确定要注销账号吗？此操作不可恢复！", "警告", { type: "warning" });
    await userApi.deleteAccount();
    wsManager.disconnect();
    userStore.logout();
    router.push("/login");
  } catch (e) {}
}

async function loadDeviceList() {
  try {
    const res = await userApi.getSessions();
    deviceList.value = res.data;
  } catch (e) {
    console.error("加载设备列表失败", e);
  }
}

async function kickDevice(sessionId) {
  try {
    await ElMessageBox.confirm("确定要踢出该设备吗？", "提示", { type: "warning" });
    await userApi.kickSession(sessionId);
    await loadDeviceList();
    ElMessage.success("已踢出该设备");
  } catch (e) {}
}

async function logoutAllOther() {
  try {
    await ElMessageBox.confirm("确定要踢出所有其他设备吗？", "提示", { type: "warning" });
    const res = await userApi.logoutAllOther();
    await loadDeviceList();
    ElMessage.success(res.data.message);
  } catch (e) {}
}

async function handleImageUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await chatApi.uploadFile(formData);
    wsManager.sendMessage(chatStore.currentConversation, "", "image", res.data.url, res.data.name, res.data.size);
  } catch (e) {
    ElMessage.error("图片上传失败");
  }
  return false;
}

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await chatApi.uploadFile(formData);
    wsManager.sendMessage(chatStore.currentConversation, "", "file", res.data.url, res.data.name, res.data.size);
  } catch (e) {
    ElMessage.error("文件上传失败");
  }
  return false;
}

function openImagePreview(url) {
  imagePreviewUrl.value = url;
}

function closeImagePreview() {
  imagePreviewUrl.value = null;
}

function downloadFile(url, name) {
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
}

const canEditMessage = computed(() => {
  const msg = contextMenu.message;
  if (!msg) return false;
  if (msg.sender.id !== userStore.user?.id) return false;
  if (msg.is_recalled) return false;
  if (msg.message_type !== 'text') return false;
  const timeDiff = (Date.now() - new Date(msg.created_at).getTime()) / 1000;
  return timeDiff <= 120;
});

function showContextMenu(e, msg) {
  contextMenu.visible = true;
  const menuWidth = 180;
  const menuHeight = 200;
  let x = e.clientX;
  let y = e.clientY;
  if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 10;
  if (y + menuHeight > window.innerHeight) y = window.innerHeight - menuHeight - 10;
  contextMenu.x = x;
  contextMenu.y = y;
  contextMenu.message = msg;
}

function hideContextMenu() {
  contextMenu.visible = false;
}

function showConvContextMenu(e, conv) {
  convContextMenu.visible = true;
  const menuWidth = 180;
  const menuHeight = 200;
  let x = e.clientX;
  let y = e.clientY;
  if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 10;
  if (y + menuHeight > window.innerHeight) y = window.innerHeight - menuHeight - 10;
  convContextMenu.x = x;
  convContextMenu.y = y;
  convContextMenu.conversation = conv;
}

function hideConvContextMenu() {
  convContextMenu.visible = false;
}

function showFriendContextMenu(e, friendship) {
  friendContextMenu.visible = true;
  const menuWidth = 180;
  const menuHeight = 200;
  let x = e.clientX;
  let y = e.clientY;
  if (x + menuWidth > window.innerWidth) x = window.innerWidth - menuWidth - 10;
  if (y + menuHeight > window.innerHeight) y = window.innerHeight - menuHeight - 10;
  friendContextMenu.x = x;
  friendContextMenu.y = y;
  friendContextMenu.friendship = friendship;
}

function hideFriendContextMenu() {
  friendContextMenu.visible = false;
}

function recallMessage() {
  if (contextMenu.message) {
    wsManager.recallMessage(contextMenu.message.id);
  }
  hideContextMenu();
}

const editingMessage = ref(null);
const editingMessageContent = ref("");

function editMessage() {
  if (!contextMenu.message) return;
  editingMessage.value = contextMenu.message;
  editingMessageContent.value = contextMenu.message.content;
  hideContextMenu();
}

async function saveEditMessage() {
  if (!editingMessage.value || !editingMessageContent.value.trim()) return;
  try {
    await chatApi.editMessage(editingMessage.value.id, editingMessageContent.value.trim());
    const msgs = chatStore.messages[chatStore.currentConversation];
    const idx = msgs.findIndex(m => m.id === editingMessage.value.id);
    if (idx !== -1) {
      msgs[idx].content = editingMessageContent.value.trim();
      msgs[idx].edited_at = new Date().toISOString();
    }
    editingMessage.value = null;
    editingMessageContent.value = "";
    ElMessage.success("消息已编辑");
  } catch (e) {
    ElMessage.error(e.response?.data?.error || "编辑失败");
  }
}

function cancelEditMessage() {
  editingMessage.value = null;
  editingMessageContent.value = "";
}

function replyMessage() {
  if (contextMenu.message) {
    replyingTo.value = contextMenu.message;
  }
  hideContextMenu();
}

async function forwardMessage() {
  if (contextMenu.message) {
    selectedForwardConv.value = null;
    showForwardDialog.value = true;
  }
  hideContextMenu();
}

async function handleForward() {
  if (!selectedForwardConv.value || !contextMenu.message) return;
  try {
    await chatApi.forwardMessage(contextMenu.message.id, selectedForwardConv.value);
    ElMessage.success("转发成功");
    showForwardDialog.value = false;
  } catch (e) {
    ElMessage.error("转发失败");
  }
}

async function favoriteMessage() {
  if (contextMenu.message) {
    try {
      await chatApi.favoriteMessage(contextMenu.message.id);
      ElMessage.success("收藏成功");
    } catch (e) {
      ElMessage.error("收藏失败");
    }
  }
  hideContextMenu();
}

function copyMessage() {
  if (contextMenu.message) {
    navigator.clipboard.writeText(contextMenu.message.content);
    ElMessage.success("已复制");
  }
  hideContextMenu();
}

async function togglePinConversation() {
  if (convContextMenu.conversation) {
    try {
      await chatApi.pinConversation(convContextMenu.conversation.id);
      await chatStore.fetchConversations();
      ElMessage.success(convContextMenu.conversation.is_pinned ? "已取消置顶" : "已置顶");
    } catch (e) {
      ElMessage.error("操作失败");
    }
  }
  hideConvContextMenu();
}

async function toggleMuteConversation() {
  if (convContextMenu.conversation) {
    try {
      await chatApi.muteConversation(convContextMenu.conversation.id);
      await chatStore.fetchConversations();
      ElMessage.success(convContextMenu.conversation.is_muted ? "已取消免打扰" : "已设置免打扰");
    } catch (e) {
      ElMessage.error("操作失败");
    }
  }
  hideConvContextMenu();
}

async function deleteConversation() {
  if (convContextMenu.conversation) {
    try {
      await ElMessageBox.confirm("确定要删除此会话吗？", "提示", { type: "warning" });
      await chatApi.hideConversation(convContextMenu.conversation.id);
      await chatStore.fetchConversations();
      if (chatStore.currentConversation === convContextMenu.conversation.id) {
        chatStore.currentConversation = null;
      }
      ElMessage.success("已删除");
    } catch (e) {}
  }
  hideConvContextMenu();
}

function openRemarkDialog() {
  if (friendContextMenu.friendship) {
    remarkInput.value = friendContextMenu.friendship.remark || "";
    showRemarkDialog.value = true;
  }
  hideFriendContextMenu();
}

async function handleSetRemark() {
  if (friendContextMenu.friendship) {
    try {
      await chatApi.setFriendRemark(friendContextMenu.friendship.friend.id, remarkInput.value);
      await chatStore.fetchFriends();
      ElMessage.success("备注已设置");
      showRemarkDialog.value = false;
    } catch (e) {
      ElMessage.error("设置失败");
    }
  }
}

async function deleteFriend() {
  if (friendContextMenu.friendship) {
    try {
      await ElMessageBox.confirm("确定要删除此好友吗？", "提示", { type: "warning" });
      await chatApi.deleteFriend(friendContextMenu.friendship.friend.id);
      await chatStore.fetchFriends();
      ElMessage.success("已删除好友");
    } catch (e) {}
  }
  hideFriendContextMenu();
}

async function blockFriend() {
  if (friendContextMenu.friendship) {
    try {
      await ElMessageBox.confirm("确定要拉黑此用户吗？", "提示", { type: "warning" });
      const friendId = friendContextMenu.friendship.friend.id;
      await chatApi.blockUser(friendId);
      await chatStore.fetchFriends();
      const blockedConv = chatStore.conversations.find(
        c => c.type === 'private' && c.members?.some(m => m.user.id === friendId)
      );
      if (blockedConv) {
        chatStore.removeConversation(blockedConv.id);
      }
      ElMessage.success("已拉黑");
    } catch (e) {}
  }
  hideFriendContextMenu();
}

async function loadFavorites() {
  try {
    const res = await chatApi.getFavoriteMessages();
    favoriteMessages.value = res.data;
  } catch (e) {
    ElMessage.error("加载收藏失败");
  }
}

async function loadBlacklist() {
  try {
    const res = await chatApi.getBlacklist();
    blacklist.value = res.data;
  } catch (e) {
    ElMessage.error("加载黑名单失败");
  }
}

async function unblockUser(userId) {
  try {
    await chatApi.unblockUser(userId);
    blacklist.value = blacklist.value.filter(item => item.blocked_user.id !== userId);
    ElMessage.success("已取消拉黑");
  } catch (e) {
    ElMessage.error("取消拉黑失败");
  }
}

async function handleGroupAvatarUpload(file) {
  if (!currentConv.value) return false;
  const formData = new FormData();
  formData.append("file", file);
  try {
    await chatApi.uploadGroupAvatar(currentConv.value.id, formData);
    await chatStore.fetchConversations();
    ElMessage.success("群头像已更新");
  } catch (e) {
    ElMessage.error("上传失败");
  }
  return false;
}

async function handleSetAnnouncement() {
  if (!currentConv.value || !announcementInput.value.trim()) return;
  try {
    await chatApi.setGroupAnnouncement(currentConv.value.id, announcementInput.value.trim());
    await chatStore.fetchConversations();
    ElMessage.success("群公告已设置");
    announcementInput.value = "";
  } catch (e) {
    ElMessage.error("设置失败");
  }
}

async function handleMemberAction(action, member) {
  if (!currentConv.value) return;
  try {
    if (action === "setAdmin" || action === "removeAdmin") {
      const isAdmin = action === "setAdmin";
      await chatApi.setGroupAdmin(currentConv.value.id, member.user.id, isAdmin);
      await chatStore.fetchConversations();
      ElMessage.success(isAdmin ? "已设为管理员" : "已取消管理员");
    } else if (action === "mute" || action === "unmute") {
      const isMuted = action === "mute";
      await chatApi.muteGroupMember(currentConv.value.id, member.user.id, isMuted);
      await chatStore.fetchConversations();
      ElMessage.success(isMuted ? "已禁言" : "已解除禁言");
    } else if (action === "transferOwner") {
      await ElMessageBox.confirm(
        `确定要将群主转让给 ${member.user.username} 吗？转让后您将成为普通成员。`,
        "转让群主",
        { type: "warning" }
      );
      await chatApi.transferGroupOwner(currentConv.value.id, member.user.id);
      await chatStore.fetchConversations();
      showGroupSettings.value = false;
      ElMessage.success("群主已转让");
    } else if (action === "kick") {
      await ElMessageBox.confirm(
        `确定要移除成员 ${member.user.username} 吗？`,
        "移除成员",
        { type: "warning" }
      );
      await chatApi.kickGroupMember(currentConv.value.id, member.user.id);
      await chatStore.fetchConversations();
      ElMessage.success("已移除成员");
    }
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("操作失败");
    }
  }
}

function startEditGroupName() {
  editingGroupName.value = currentConv.value?.name || "";
  isEditingGroupName.value = true;
}

async function saveGroupName() {
  if (!currentConv.value || !editingGroupName.value.trim()) return;
  try {
    await chatApi.updateGroupName(currentConv.value.id, editingGroupName.value.trim());
    await chatStore.fetchConversations();
    isEditingGroupName.value = false;
    ElMessage.success("群名称已更新");
  } catch (e) {
    ElMessage.error("修改失败");
  }
}

function copyInviteCode() {
  if (currentConv.value?.invite_code) {
    navigator.clipboard.writeText(currentConv.value.invite_code);
    ElMessage.success("邀请码已复制");
  }
}

async function handleStatusChange(status) {
  try {
    await userApi.updateProfile({ status });
    userStore.user.status = status;
    ElMessage.success("状态已更新");
  } catch (e) {
    ElMessage.error("状态更新失败");
  }
}

async function acceptRequest(requestId) {
  try {
    await chatApi.acceptFriendRequest(requestId);
    await chatStore.fetchFriends();
    await chatStore.fetchFriendRequests();
    ElMessage.success("已接受好友申请");
  } catch (e) {
    ElMessage.error("操作失败");
  }
}

async function rejectRequest(requestId) {
  try {
    await chatApi.rejectFriendRequest(requestId);
    await chatStore.fetchFriendRequests();
    ElMessage.success("已拒绝");
  } catch (e) {
    ElMessage.error("操作失败");
  }
}

function showUserProfile(user) {
  viewingUser.value = user;
  showUserProfileDialog.value = true;
}

function openRemarkFromProfile(userId) {
  const friendship = chatStore.friends.find(f => f.friend.id === userId);
  if (friendship) {
    friendContextMenu.friendship = friendship;
    remarkInput.value = friendship.remark || "";
    showRemarkDialog.value = true;
  }
  showUserProfileDialog.value = false;
}

async function blockUserFromProfile(userId) {
  try {
    await ElMessageBox.confirm("确定要拉黑此用户吗？", "提示", { type: "warning" });
    await chatApi.blockUser(userId);
    await chatStore.fetchFriends();
    const blockedConv = chatStore.conversations.find(
      c => c.type === 'private' && c.members?.some(m => m.user.id === userId)
    );
    if (blockedConv) {
      chatStore.removeConversation(blockedConv.id);
    }
    showUserProfileDialog.value = false;
    ElMessage.success("已拉黑");
  } catch (e) {}
}

async function handleProfileAvatarUpload(file) {
  const formData = new FormData();
  formData.append("avatar", file);
  try {
    await userApi.updateProfile(formData);
    await userStore.fetchProfile();
    profileEditData.avatar = userStore.user?.avatar;
    ElMessage.success("头像已更新");
  } catch (e) {
    ElMessage.error("头像上传失败");
  }
  return false;
}

async function saveProfile() {
  try {
    await userApi.updateProfile({
      signature: profileEditData.signature,
      status: profileEditData.status,
    });
    await userStore.fetchProfile();
    ElMessage.success("资料已保存");
    showProfileEdit.value = false;
  } catch (e) {
    ElMessage.error("保存失败");
  }
}

async function handleJoinGroup() {
  if (!inviteCodeInput.value.trim()) return;
  try {
    const res = await chatApi.joinGroupByInviteCode(inviteCodeInput.value.trim());
    await chatStore.fetchConversations();
    wsManager.reconnect();
    showJoinGroup.value = false;
    inviteCodeInput.value = "";
    if (res.data?.id) {
      chatStore.currentConversation = res.data.id;
      await chatStore.fetchMessages(res.data.id);
      await nextTick();
      scrollToBottom();
    }
    ElMessage.success("已加入群聊");
  } catch (e) {
    ElMessage.error("加入失败，请检查邀请码");
  }
}

async function kickMember(memberId) {
  if (!currentConv.value) return;
  try {
    await ElMessageBox.confirm("确定要移除该成员吗？", "提示", { type: "warning" });
    await chatApi.kickGroupMember(currentConv.value.id, memberId);
    await chatStore.fetchConversations();
    ElMessage.success("已移除");
  } catch (e) {}
}

async function leaveGroup() {
  if (!currentConv.value) return;
  try {
    await ElMessageBox.confirm("确定要退出群聊吗？", "提示", { type: "warning" });
    await chatApi.leaveGroup(currentConv.value.id);
    chatStore.removeConversation(currentConv.value.id);
    showGroupSettings.value = false;
    ElMessage.success("已退出群聊");
  } catch (e) {
    ElMessage.error("退出失败");
  }
}

async function dissolveGroup() {
  if (!currentConv.value) return;
  try {
    await ElMessageBox.confirm("确定要解散群聊吗？此操作不可恢复！", "警告", { type: "warning" });
    await chatApi.dissolveGroup(currentConv.value.id);
    chatStore.removeConversation(currentConv.value.id);
    showGroupSettings.value = false;
    ElMessage.success("群聊已解散");
  } catch (e) {
    ElMessage.error("解散失败");
  }
}

async function loadFriendGroups() {
  try {
    const res = await chatApi.getFriendGroups();
    friendGroupsList.value = res.data;
    res.data.forEach(g => {
      if (expandedGroups[g.id] === undefined) {
        expandedGroups[g.id] = true;
      }
    });
  } catch (e) {
    console.error("加载好友分组失败", e);
  }
}

function getGroupFriends(groupId) {
  let friends = chatStore.friends.filter(f => f.group?.id === groupId);
  if (showOnlineOnly.value) friends = friends.filter(f => f.friend.is_online);
  return friends;
}

function toggleGroupExpand(groupId) {
  expandedGroups[groupId] = !expandedGroups[groupId];
}

async function handleCreateFriendGroup() {
  if (!newFriendGroupName.value.trim()) return;
  try {
    await chatApi.createFriendGroup(newFriendGroupName.value.trim());
    await loadFriendGroups();
    ElMessage.success("分组已创建");
    showCreateFriendGroup.value = false;
    newFriendGroupName.value = "";
  } catch (e) {
    ElMessage.error("创建失败");
  }
}

async function saveFriendTags() {
  if (!settingTagsFriendId.value) return;
  try {
    await chatApi.setFriendTags(settingTagsFriendId.value, friendTagsInput.value);
    await chatStore.fetchConversations();
    ElMessage.success("标签已保存");
    showSetTags.value = false;
  } catch (e) {
    ElMessage.error("保存失败");
  }
}

function openSetTags(friendId, currentTags = "") {
  settingTagsFriendId.value = friendId;
  friendTagsInput.value = currentTags;
  showSetTags.value = true;
}

function openTagsDialog() {
  if (friendContextMenu.friendship) {
    settingTagsFriendId.value = friendContextMenu.friendship.friend.id;
    friendTagsInput.value = friendContextMenu.friendship.tags || "";
    showSetTags.value = true;
  }
  hideFriendContextMenu();
}

async function saveMyNickname() {
  if (!currentConv.value) return;
  try {
    await chatApi.setGroupNickname(currentConv.value.id, myNickname.value);
    await chatStore.fetchConversations();
    ElMessage.success("群昵称已保存");
  } catch (e) {
    ElMessage.error("保存失败");
  }
}

async function loadTransferRecords() {
  if (!currentConv.value) return;
  try {
    const res = await chatApi.getTransferRecords(currentConv.value.id);
    transferRecords.value = res.data;
  } catch (e) {
    console.error("加载转让记录失败", e);
  }
}

async function moveToGroup(groupId) {
  if (!friendContextMenu.friendship) return;
  try {
    await chatApi.setFriendGroup(friendContextMenu.friendship.friend.id, groupId);
    await chatStore.fetchFriends();
    ElMessage.success("已移动分组");
  } catch (e) {
    ElMessage.error("移动失败");
  }
  hideFriendContextMenu();
}

async function handleScroll() {
  if (!messageListRef.value || !chatStore.currentConversation || loadingMore.value || !hasMoreMessages.value) return;

  const { scrollTop } = messageListRef.value;
  if (scrollTop < 50) {
    loadingMore.value = true;
    const msgs = chatStore.messages[chatStore.currentConversation] || [];
    const oldestMsg = msgs[0];
    if (!oldestMsg) {
      loadingMore.value = false;
      return;
    }

    try {
      const res = await chatApi.getMessages(chatStore.currentConversation, oldestMsg.id, 50);
      if (res.data.length === 0) {
        hasMoreMessages.value = false;
      } else {
        const prevHeight = messageListRef.value.scrollHeight;
        chatStore.messages[chatStore.currentConversation] = [...res.data, ...msgs];
        await nextTick();
        const newHeight = messageListRef.value.scrollHeight;
        messageListRef.value.scrollTop = newHeight - prevHeight;
      }
    } catch (e) {
      console.error("加载更多消息失败", e);
    }
    loadingMore.value = false;
  }
}

watch(currentMessages, () => {
  nextTick(scrollToBottom);
}, { deep: true });

watch(showAddFriend, (val) => {
  if (val) loadUsers();
});

watch(activeTab, (val) => {
  if (val === "friends") {
    chatStore.fetchFriendRequests();
  }
});

watch(showProfileEdit, (val) => {
  if (val) {
    profileEditData.signature = userStore.user?.signature || "";
    profileEditData.status = userStore.user?.status || "online";
    profileEditData.avatar = userStore.user?.avatar || "";
  }
});

watch(showGroupSettings, (val) => {
  if (val && currentConv.value) {
    loadTransferRecords();
    const member = currentConv.value.members?.find(m => m.user.id === userStore.user?.id);
    myNickname.value = member?.nickname || "";
  }
});

watch(showDeviceManager, (val) => {
  if (val) {
    loadDeviceList();
  }
});

document.addEventListener("click", (e) => {
  hideContextMenu();
  hideConvContextMenu();
  hideFriendContextMenu();
  if (!e.target.closest(".el-popover") && !e.target.closest(".el-button")) {
    showEmojiPicker.value = false;
  }
});

async function loadUsers() {
  try {
    const res = await userApi.getUsers();
    allUsers.value = res.data;
  } catch (error) {
    console.error("加载用户列表失败:", error);
  }
}

onMounted(async () => {
  try {
    await userStore.fetchProfile();
    await chatStore.fetchConversations();
    await chatStore.fetchFriends();
    await chatStore.fetchFriendRequests();
    await loadFriendGroups();
    wsManager.connect();
    if (isDarkMode.value) {
      document.body.classList.add("dark-mode");
    }
  } catch (error) {
    console.error("初始化失败:", error);
  } finally {
    initialLoading.value = false;
  }

  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth <= 768;
    if (!isMobile.value) {
      sidebarCollapsed.value = false;
    }
  });

  const chatMainEl = document.querySelector('.chat-main');
  if (chatMainEl) {
    chatMainEl.addEventListener('dragenter', () => { isDragging.value = true; });
    chatMainEl.addEventListener('dragleave', (e) => {
      if (!chatMainEl.contains(e.relatedTarget)) {
        isDragging.value = false;
      }
    });
  }
});

onUnmounted(() => {
  document.removeEventListener("click", hideContextMenu);
});
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: var(--color-bg-secondary);
  transition: background var(--transition-normal);
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-bg-sidebar);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border);
  transition: background var(--transition-normal), border-color var(--transition-normal);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  cursor: pointer;
}

.avatar-wrapper {
  position: relative;
}

.avatar-wrapper :deep(.el-dropdown) {
  position: absolute;
  bottom: 0;
  right: 0;
}

.user-avatar {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  font-weight: 600;
}

.user-info h3 {
  color: white;
  margin: 0;
  font-size: var(--font-lg);
  font-weight: 600;
}

.user-info .status {
  color: rgba(255, 255, 255, 0.8);
  font-size: var(--font-sm);
}

.menu-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
}

.menu-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.search-box {
  padding: var(--spacing-md) var(--spacing-lg);
  position: relative;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: var(--radius-xl);
  background: var(--color-bg-secondary);
  box-shadow: none;
}

.sidebar-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sidebar-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 var(--spacing-lg);
}

.sidebar-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.request-badge {
  margin-left: var(--spacing-xs);
}

.sidebar-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.sidebar-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.conversation-list,
.friend-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.conversation-item,
.friend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.conversation-item:hover,
.friend-item:hover {
  background: var(--color-bg-hover);
}

.conversation-item.active {
  background: var(--color-bg-active);
}

.conversation-item.pinned {
  background: #fef3c7;
}

.dark-mode .conversation-item.pinned {
  background: #3d3a1a;
}

.conv-avatar,
.friend-avatar {
  position: relative;
}

.conv-avatar .el-avatar,
.friend-avatar .el-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
}

.online-indicator,
.status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
}

.unread-badge {
  position: absolute;
  top: -5px;
  right: -5px;
}

.unread-badge :deep(.el-badge__content) {
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
}

.online-indicator,
.status-dot.online {
  background: var(--color-success);
}

.status-dot.offline {
  background: var(--color-text-tertiary);
}

.conv-info {
  flex: 1;
  overflow: hidden;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.conv-name {
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.pin-icon {
  color: var(--color-warning);
  font-size: var(--font-sm);
}

.mute-icon {
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
  margin-right: var(--spacing-xs);
}

.conv-time {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.conv-preview {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
}

.recalled-text {
  color: var(--color-text-tertiary);
  font-style: italic;
}

.friend-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.friend-name {
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: var(--font-md);
}

.friend-status {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.chat-btn {
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.friend-item:hover .chat-btn {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--color-text-tertiary);
}

.empty-state p {
  margin-top: var(--spacing-md);
  font-size: var(--font-md);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-chat);
  transition: background var(--transition-normal);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  transition: background var(--transition-normal), border-color var(--transition-normal);
}

.chat-header-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.chat-header-info .el-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
}

.chat-header-text h3 {
  margin: 0;
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.chat-status {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.chat-header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  color: var(--color-text-tertiary);
  font-size: var(--font-md);
}

.message-wrapper {
  display: flex;
  gap: var(--spacing-md);
  max-width: 70%;
  margin-bottom: var(--spacing-lg);
}

.message-wrapper.consecutive {
  margin-top: calc(-1 * var(--spacing-sm));
  gap: var(--spacing-md);
}

.message-wrapper.consecutive .msg-avatar {
  visibility: hidden;
}

.message-wrapper.consecutive .message-header {
  display: none;
}

.message-wrapper.self {
  flex-direction: row-reverse;
  align-self: flex-end;
  margin-left: auto;
}

.message-wrapper.other {
  align-self: flex-start;
}

.message-wrapper.system {
  align-self: center;
  max-width: 100%;
  justify-content: center;
}

.msg-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
}

.message-wrapper.self .msg-avatar {
  background: linear-gradient(135deg, var(--color-success) 0%, #16a34a 100%);
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.message-wrapper.self .message-content {
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.message-wrapper.self .message-header {
  flex-direction: row-reverse;
}

.message-sender {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.message-time {
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
}

.reply-preview {
  background: var(--color-bg-secondary);
  padding: var(--spacing-xs) 10px;
  border-radius: var(--spacing-sm);
  border-left: 3px solid var(--color-primary);
  margin-bottom: var(--spacing-xs);
  max-width: 200px;
}

.reply-to-name {
  font-size: var(--font-sm);
  color: var(--color-primary);
  font-weight: 500;
  display: block;
}

.reply-to-content {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.message-bubble {
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: 18px;
  font-size: var(--font-md);
  line-height: 1.5;
  word-break: break-word;
  background: var(--color-bg-message-other);
  box-shadow: var(--color-shadow-sm);
  transition: background var(--transition-normal);
  display: inline-block;
  width: fit-content;
  max-width: 100%;
}

.message-wrapper.self .message-bubble {
  background: var(--color-bg-message-self);
  color: white;
}

.message-bubble :deep(.mention) {
  color: var(--color-primary);
  font-weight: 500;
  background: var(--color-primary-bg);
  padding: 0 2px;
  border-radius: 2px;
}

.message-wrapper.self .message-bubble :deep(.mention) {
  color: #fef3c7;
  background: rgba(254, 243, 199, 0.2);
}

.message-bubble.recalled {
  color: var(--color-text-tertiary);
  font-style: italic;
  background: var(--color-bg-secondary);
}

.system-message {
  width: 100%;
  text-align: center;
  padding: var(--spacing-sm) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}

.system-message span {
  background: var(--color-bg-secondary);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-lg);
}

.edited-mark {
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  margin-left: var(--spacing-xs);
}

.message-bubble.image-message {
  padding: var(--spacing-xs);
  background: transparent;
  box-shadow: none;
}

.message-bubble.image-message img {
  max-width: 300px;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.image-loading-placeholder {
  width: 200px;
  height: 150px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

.image-error-placeholder {
  width: 200px;
  height: 150px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  gap: var(--spacing-xs);
  font-size: var(--font-sm);
}

.message-bubble.file-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  min-width: 200px;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: var(--font-md);
  font-weight: 500;
}

.file-size {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.message-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-xs);
  padding-top: var(--spacing-xs);
}

.read-icon {
  color: var(--color-primary);
}

.error-icon {
  color: var(--color-danger);
  cursor: pointer;
}

.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--color-text-tertiary);
}

.empty-messages p {
  margin-top: var(--spacing-lg);
  font-size: var(--font-md);
}

.messages-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--color-primary);
  font-size: 24px;
}

.message-input-area {
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--color-bg-primary);
  border-top: 1px solid var(--color-border);
  transition: background var(--transition-normal), border-color var(--transition-normal);
}

.reply-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-bg-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.reply-bar-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.reply-label {
  font-size: var(--font-sm);
  color: var(--color-primary);
  font-weight: 500;
}

.reply-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.input-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-md) var(--spacing-sm) var(--spacing-md) var(--spacing-xl);
  transition: background var(--transition-normal);
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  background: transparent;
  box-shadow: none !important;
  padding: 0;
  font-size: 15px;
  border: none;
  resize: none;
  line-height: 1.5;
  min-height: 24px;
}

.message-input :deep(.el-textarea__inner:focus) {
  box-shadow: none !important;
}

.send-btn {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border: none;
}

.send-btn:hover {
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--color-bg-tertiary);
}

.upload-progress {
  margin-bottom: var(--spacing-sm);
}

.emoji-picker {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: var(--spacing-xs);
  background: var(--color-bg-primary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
}

.emoji-item {
  font-size: var(--font-xl);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  text-align: center;
  transition: background var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 1;
}

.emoji-item:hover {
  background: var(--color-bg-hover);
}

.emoji-btn-icon {
  font-size: 18px;
  line-height: 1;
}

.mention-list {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 60px;
  background: var(--color-bg-primary);
  border-radius: var(--spacing-sm);
  box-shadow: var(--color-shadow-lg);
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: var(--spacing-sm);
  z-index: 10;
}

.mention-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.mention-item:hover {
  background: var(--color-bg-hover);
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.welcome-hamburger-btn {
  position: absolute;
  top: var(--spacing-lg);
  left: var(--spacing-lg);
  z-index: 10;
}

.welcome-content {
  text-align: center;
}

.welcome-icon {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-xl);
  color: white;
}

.welcome-content h2 {
  font-size: var(--font-3xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-md);
}

.welcome-content p {
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-2xl);
  font-size: var(--font-lg);
}

.welcome-actions {
  display: flex;
  justify-content: center;
}

.welcome-actions .el-button {
  height: 44px;
  padding: 0 var(--spacing-xl);
  border-radius: 22px;
  font-size: 15px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border: none;
}

.modern-dialog :deep(.el-dialog__header) {
  padding: var(--spacing-xl) var(--spacing-xl) 0;
}

.modern-dialog :deep(.el-dialog__body) {
  padding: var(--spacing-xl);
}

.user-search-results {
  max-height: 300px;
  overflow-y: auto;
}

.user-search-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
  transition: background var(--transition-fast);
}

.user-search-item:hover {
  background: var(--color-bg-hover);
}

.user-search-item .el-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
}

.user-name {
  flex: 1;
  font-weight: 500;
}

.member-select {
  width: 100%;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-option .el-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-manager {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.device-header span {
  font-weight: 600;
  color: var(--color-text-primary);
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-height: 400px;
  overflow-y: auto;
}

.device-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.device-item.current {
  background: var(--color-primary-bg);
  border: 1px solid var(--color-primary);
}

.device-icon {
  width: 48px;
  height: 48px;
  background: var(--color-bg-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

.device-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-weight: 500;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.device-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.empty-devices {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-tertiary);
}

.empty-devices p {
  margin-top: var(--spacing-md);
}

.search-results {
  margin-top: var(--spacing-lg);
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.search-result-item:hover {
  background: var(--color-bg-hover);
}

.search-result-sender {
  font-weight: 500;
  margin-bottom: var(--spacing-xs);
}

.search-result-content {
  color: var(--color-text-secondary);
  font-size: var(--font-md);
}

.search-result-content :deep(mark) {
  background: rgba(245, 158, 11, 0.3);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.search-result-time {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-xs);
}

.forward-list {
  max-height: 400px;
  overflow-y: auto;
}

.forward-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.forward-item:hover {
  background: var(--color-bg-hover);
}

.forward-item.selected {
  background: var(--color-bg-active);
}

.forward-name {
  font-weight: 500;
}

.favorites-list {
  max-height: 400px;
  overflow-y: auto;
}

.favorite-item {
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
  background: var(--color-bg-secondary);
  margin-bottom: var(--spacing-sm);
}

.favorite-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.favorite-sender {
  font-weight: 500;
  font-size: var(--font-md);
}

.favorite-time {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.favorite-content {
  color: var(--color-text-secondary);
  font-size: var(--font-md);
}

.blacklist-container {
  max-height: 400px;
  overflow-y: auto;
}

.blacklist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
  background: var(--color-bg-secondary);
  margin-bottom: var(--spacing-sm);
}

.blacklist-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.blacklist-info {
  display: flex;
  flex-direction: column;
}

.blacklist-name {
  font-weight: 500;
}

.blacklist-time {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
}

.group-settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.group-info {
  text-align: center;
}

.group-avatar-section {
  display: inline-block;
  position: relative;
}

.group-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.avatar-upload-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: var(--font-sm);
  padding: 2px 0;
  border-radius: 0 0 40px 40px;
}

.group-name-section {
  margin-top: var(--spacing-md);
}

.group-name-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.group-name-edit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.group-name {
  font-size: var(--font-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.group-invite-code {
  margin-top: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.invite-code-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-sm);
}

.invite-code-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
}

.invite-code-value {
  font-size: var(--font-xl);
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 2px;
  font-family: monospace;
}

.invite-code-hint {
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  text-align: center;
  margin-top: var(--spacing-sm);
}

.group-announcement {
  background: var(--color-bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--spacing-sm);
}

.group-announcement h4 {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-md);
  color: var(--color-text-primary);
}

.group-announcement p {
  margin: 0;
  font-size: var(--font-md);
  color: var(--color-text-secondary);
}

.announcement-edit {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
}

.announcement-edit .el-textarea {
  flex: 1;
}

.group-members h4 {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-md);
  color: var(--color-text-primary);
}

.member-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  max-height: 300px;
  overflow-y: auto;
}

.member-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--spacing-sm);
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.member-name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.member-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.member-role {
  font-size: var(--font-xs);
  padding: 1px var(--spacing-xs);
  border-radius: var(--spacing-xs);
}

.member-role.owner {
  background: #fef3c7;
  color: #d97706;
}

.member-role.admin {
  background: #dbeafe;
  color: #2563eb;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.context-menu {
  position: fixed;
  background: var(--color-bg-primary);
  border-radius: var(--spacing-sm);
  box-shadow: var(--color-shadow-lg);
  padding: var(--spacing-sm) 0;
  z-index: 9999;
  min-width: 120px;
}

.context-menu-item {
  padding: var(--spacing-sm) var(--spacing-lg);
  cursor: pointer;
  font-size: var(--font-md);
  transition: background var(--transition-fast);
}

.context-menu-item:hover {
  background: var(--color-bg-hover);
}

.context-menu-item.danger {
  color: var(--color-danger);
}

.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  cursor: pointer;
}

.image-preview-img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.image-preview-overlay .close-btn {
  position: absolute;
  top: var(--spacing-xl);
  right: var(--spacing-xl);
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
}

.status-indicator-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  z-index: 1;
}

.status-indicator-dot.online {
  background: var(--color-success);
}

.status-indicator-dot.busy {
  background: var(--color-danger);
}

.status-indicator-dot.away {
  background: var(--color-warning);
}

.status-indicator-dot.invisible {
  background: var(--color-text-tertiary);
}

.status-option-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: var(--spacing-xs);
}

.status-option-dot.online {
  background: var(--color-success);
}

.status-option-dot.busy {
  background: var(--color-danger);
}

.status-option-dot.away {
  background: var(--color-warning);
}

.status-option-dot.invisible {
  background: var(--color-text-tertiary);
}

.search-results-dropdown {
  position: absolute;
  top: 100%;
  left: var(--spacing-lg);
  right: var(--spacing-lg);
  background: var(--color-bg-primary);
  border-radius: var(--spacing-sm);
  box-shadow: var(--color-shadow-lg);
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
}

.search-group-title {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-xs);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  font-weight: 600;
}

.search-result-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  font-size: var(--font-md);
}

.search-result-row:hover {
  background: var(--color-bg-hover);
}

.friend-requests-section {
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fef3c7;
  border-radius: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.dark-mode .friend-requests-section {
  background: #3d3a1a;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.section-title {
  font-weight: 600;
  font-size: var(--font-md);
  color: var(--color-text-primary);
}

.request-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.request-item:last-child {
  border-bottom: none;
}

.request-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.request-name {
  font-weight: 500;
  font-size: var(--font-md);
  color: var(--color-text-primary);
}

.request-time {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.request-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.friend-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
}

.online-count {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.friend-group-actions {
  padding: 0 var(--spacing-md) var(--spacing-sm);
}

.friend-group-section {
  margin-bottom: var(--spacing-xs);
}

.group-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  border-radius: var(--spacing-sm);
  font-weight: 500;
  font-size: var(--font-md);
  color: var(--color-text-primary);
  transition: background var(--transition-fast);
}

.group-header:hover {
  background: var(--color-bg-hover);
}

.group-header .el-icon {
  transition: transform var(--transition-fast);
}

.group-header .el-icon.expanded {
  transform: rotate(90deg);
}

.group-count {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.group-friends {
  padding-left: var(--spacing-sm);
}

.profile-edit-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xl);
}

.profile-avatar-section {
  position: relative;
  display: inline-block;
}

.profile-edit-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.profile-form {
  width: 100%;
}

.user-profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.profile-card-avatar {
  position: relative;
}

.profile-card-avatar .el-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: white;
  font-weight: 600;
}

.status-dot-lg {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border: 3px solid white;
  border-radius: 50%;
}

.status-dot-lg.online {
  background: var(--color-success);
}

.status-dot-lg.offline {
  background: var(--color-text-tertiary);
}

.profile-card-info {
  text-align: center;
}

.profile-card-info h3 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.profile-signature {
  color: var(--color-text-secondary);
  font-size: var(--font-md);
  margin: var(--spacing-sm) 0 var(--spacing-xs);
}

.profile-status-text {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.profile-card-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  justify-content: center;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.group-bottom-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
}

.my-nickname {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
}

.transfer-records h4 {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-md);
  color: var(--color-text-primary);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
}

.record-text {
  color: var(--color-text-primary);
}

.record-time {
  color: var(--color-text-tertiary);
  font-size: var(--font-xs);
}

.tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
}

.tag-item {
  margin: 0;
}

.context-menu-item.has-submenu {
  position: relative;
}

.context-submenu {
  display: none;
  position: absolute;
  left: 100%;
  top: 0;
  background: var(--color-bg-primary);
  border-radius: var(--spacing-sm);
  box-shadow: var(--color-shadow-lg);
  padding: var(--spacing-sm) 0;
  min-width: 120px;
}

.context-menu-item.has-submenu:hover .context-submenu {
  display: block;
}

.message-list-enter-active {
  transition: all 0.3s ease;
}

.message-list-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  border-radius: var(--radius-md);
  pointer-events: none;
}

.drag-overlay-content {
  background: var(--color-bg-primary);
  padding: var(--spacing-2xl);
  border-radius: var(--radius-lg);
  text-align: center;
  box-shadow: var(--color-shadow-lg);
}

.drag-overlay-content p {
  margin-top: var(--spacing-sm);
  color: var(--color-text-secondary);
  font-size: var(--font-md);
}

.hamburger-btn {
  display: none;
  margin-right: var(--spacing-sm);
}

.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-overlay);
  z-index: 99;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: calc(-1 * var(--sidebar-width));
    z-index: 100;
    transition: left var(--transition-normal);
    height: 100vh;
  }

  .sidebar.expanded {
    left: 0;
  }

  .chat-area {
    width: 100%;
  }

  .hamburger-btn {
    display: inline-flex;
  }

  .mobile-overlay {
    display: block;
  }
}
</style>

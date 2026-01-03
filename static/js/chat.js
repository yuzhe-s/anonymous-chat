// 初始化Socket.IO连接
const socket = io();

// 应用状态
const AppState = {
    INIT: 'init',
    WAITING: 'waiting',
    CHATTING: 'chatting'
};

let currentState = AppState.INIT;
let currentRoomId = null;
let currentRoomKey = null;
let currentMatchType = 'random';  // 'random', 'keyword', 'private'

// 获取DOM元素
const startScreen = document.getElementById('start-screen');
const waitingScreen = document.getElementById('waiting-screen');
const chatScreen = document.getElementById('chat-screen');
const profileForm = document.getElementById('profile-form');
const joinRoomForm = document.getElementById('join-room-form');
const startMatchBtn = document.getElementById('start-match-btn');
const createRoomBtn = document.getElementById('create-room-btn');
const joinRoomBtn = document.getElementById('join-room-btn');
const cancelMatchBtn = document.getElementById('cancel-match-btn');
const leaveBtn = document.getElementById('leave-btn');
const sendBtn = document.getElementById('send-btn');
const messageInput = document.getElementById('message-input');
const messagesContainer = document.getElementById('messages');
const waitingCount = document.getElementById('waiting-count');

// 切换界面状态
function switchScreen(state) {
    startScreen.classList.remove('active');
    waitingScreen.classList.remove('active');
    chatScreen.classList.remove('active');
    profileForm.classList.remove('active');
    joinRoomForm.classList.remove('active');

    switch(state) {
        case AppState.INIT:
            startScreen.classList.add('active');
            break;
        case AppState.WAITING:
            waitingScreen.classList.add('active');
            break;
        case AppState.CHATTING:
            chatScreen.classList.add('active');
            break;
    }
    currentState = state;
}

// 显示简介表单
function showProfileForm(matchType) {
    startScreen.classList.remove('active');
    profileForm.classList.remove('active');
    joinRoomForm.classList.remove('active');
    profileForm.classList.add('active');
    currentMatchType = matchType;
}

// 显示秘钥输入表单
function showJoinRoomForm() {
    startScreen.classList.remove('active');
    profileForm.classList.remove('active');
    joinRoomForm.classList.remove('active');
    joinRoomForm.classList.add('active');
}

// 隐藏所有表单，返回主界面
function hideAllForms() {
    profileForm.classList.remove('active');
    joinRoomForm.classList.remove('active');
    startScreen.classList.add('active');
}

// 提取关键词
function extractKeywords(text) {
    if (!text) return [];
    return text.split(/\s+/)
        .map(k => k.trim())
        .filter(k => k.length >= 2);
}

// HTML转义，防止XSS攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 添加消息到聊天界面
function addMessage(content, timestamp, isOwn, isSystem = false) {
    const messageEl = document.createElement('div');

    if (isSystem) {
        messageEl.className = 'message system-message';
        messageEl.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    } else {
        messageEl.className = `message ${isOwn ? 'own' : 'other'}`;

        const time = new Date(timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageEl.innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
            <div class="message-time">${time}</div>
        `;
    }

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 添加系统消息
function addSystemMessage(content) {
    addMessage(content, null, false, true);
}

// 清空消息列表
function clearMessages() {
    messagesContainer.innerHTML = '';
}

// 禁用聊天输入
function disableChatInput() {
    messageInput.disabled = true;
    sendBtn.disabled = true;
}

// 启用聊天输入
function enableChatInput() {
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();
}

// 发送消息
function sendMessage() {
    const content = messageInput.value.trim();

    if (content && currentState === AppState.CHATTING) {
        socket.emit('send_message', { content: content });
        messageInput.value = '';
    }
}

// ========== 事件监听器 ==========

// 开始匹配按钮
startMatchBtn.addEventListener('click', () => {
    showProfileForm('keyword');
});

// 创建私密房间按钮
createRoomBtn.addEventListener('click', () => {
    showProfileForm('private');
});

// 通过秘钥加入按钮
joinRoomBtn.addEventListener('click', () => {
    showJoinRoomForm();
});

// 提交简介并开始匹配
document.getElementById('submit-profile-btn').addEventListener('click', () => {
    const bio = document.getElementById('user-bio').value.trim();
    const purpose = document.getElementById('user-purpose').value.trim();
    const keywordsText = document.getElementById('user-keywords').value.trim();
    const keywords = extractKeywords(keywordsText);

    const profileData = {
        bio: bio,
        purpose: purpose,
        keywords: keywords
    };

    if (currentMatchType === 'private') {
        // 创建私密房间
        socket.emit('create_private_room', profileData);
    } else {
        // 关键词匹配
        socket.emit('join_queue_with_profile', profileData);
    }

    profileForm.classList.add('active');
    switchScreen(AppState.WAITING);
});

// 跳过简介
document.getElementById('skip-profile-btn').addEventListener('click', () => {
    if (currentMatchType === 'private') {
        socket.emit('create_private_room', {
            bio: '',
            purpose: '',
            keywords: []
        });
    } else {
        socket.emit('join_queue');
    }
    profileForm.classList.add('active');
    switchScreen(AppState.WAITING);
});

// 通过秘钥加入房间
document.getElementById('join-by-key-btn').addEventListener('click', () => {
    const roomKey = document.getElementById('room-key-input').value.trim().toUpperCase();

    if (roomKey.length !== 8) {
        alert('秘钥必须是8位');
        return;
    }

    const bio = document.getElementById('join-bio').value.trim();
    const purpose = document.getElementById('join-purpose').value.trim();
    const keywordsText = document.getElementById('join-purpose').value.trim();
    const keywords = extractKeywords(keywordsText);

    const profileData = {
        room_key: roomKey,
        bio: bio,
        purpose: purpose,
        keywords: keywords
    };

    socket.emit('join_private_room', profileData);
    joinRoomForm.classList.add('active');
    switchScreen(AppState.WAITING);
});

// 取消加入
document.getElementById('cancel-join-btn').addEventListener('click', () => {
    hideAllForms();
});

// 取消匹配
cancelMatchBtn.addEventListener('click', () => {
    socket.disconnect();
    socket.connect();
    switchScreen(AppState.INIT);
});

// 离开房间
leaveBtn.addEventListener('click', () => {
    if (confirm('确定要离开聊天吗？')) {
        socket.emit('leave_room_event');
        switchScreen(AppState.INIT);
        clearMessages();
        enableChatInput();
        currentRoomId = null;
    }
});

// 发送按钮点击
sendBtn.addEventListener('click', sendMessage);

// 回车发送消息
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// ========== Socket.IO 事件监听 ==========

// 连接成功
socket.on('connect', () => {
    console.log('已连接到服务器');
});

// 等待匹配
socket.on('waiting', (data) => {
    console.log('等待匹配中...', data);
    if (data.waiting_count > 1) {
        waitingCount.textContent = `当前有 ${data.waiting_count} 人在等待`;
    } else {
        waitingCount.textContent = '';
    }
});

// 匹配成功
socket.on('matched', (data) => {
    console.log('匹配成功!', data);
    currentRoomId = data.room_id;
    currentMatchType = 'random';
    currentRoomKey = null;
    switchScreen(AppState.CHATTING);
    clearMessages();
    addSystemMessage('✅ 已匹配到聊天对象，开始聊天吧！');
    enableChatInput();
});

// 关键词匹配成功
socket.on('matched_with_score', (data) => {
    console.log('关键词匹配成功!', data);
    currentRoomId = data.room_id;
    currentMatchType = 'keyword';
    currentRoomKey = null;
    switchScreen(AppState.CHATTING);
    clearMessages();

    const matchScore = (data.match_score * 100).toFixed(0);
    addSystemMessage(`✅ 匹配成功！\n\n相似度：${matchScore}%\n匹配关键词：${data.keywords_matched.join('、')}\n\n开始聊天吧！`);
    enableChatInput();
});

// 私密房间创建成功
socket.on('private_room_created', (data) => {
    console.log('私密房间已创建:', data);
    currentRoomId = data.room_id;
    currentRoomKey = data.room_key;
    currentMatchType = 'private';

    switchScreen(AppState.CHATTING);
    clearMessages();
    addSystemMessage(data.message);

    // 显示秘钥
    document.getElementById('room-key-display').style.display = 'inline';
    document.getElementById('current-room-key').textContent = data.room_key;
    enableChatInput();
});

// 加入私密房间成功
socket.on('joined_private_room', (data) => {
    console.log('已加入私密房间:', data);
    currentRoomId = data.room_id;
    currentRoomKey = data.room_key;
    currentMatchType = 'private';

    switchScreen(AppState.CHATTING);
    clearMessages();

    if (data.has_history) {
        addSystemMessage('📜 正在加载历史消息...');
    } else {
        addSystemMessage('✅ 已加入私密房间，开始聊天吧！');
    }

    // 显示秘钥
    document.getElementById('room-key-display').style.display = 'inline';
    document.getElementById('current-room-key').textContent = data.room_key;
    enableChatInput();
});

// 接收历史消息
socket.on('room_history', (data) => {
    console.log('收到历史消息:', data.message_count);

    if (data.messages && data.messages.length > 0) {
        addSystemMessage(`📜 已加载 ${data.messages.length} 条历史消息\n---`);

        data.messages.forEach(msg => {
            const isOwn = msg.sender_id === window.currentUserId;
            addMessage(msg.content, msg.timestamp, isOwn);
        });

        addSystemMessage('--- 历史消息加载完毕');
    }
});

// 复制秘钥
document.getElementById('copy-key-btn').addEventListener('click', () => {
    if (currentRoomKey) {
        navigator.clipboard.writeText(currentRoomKey).then(() => {
            alert('秘钥已复制到剪贴板！\n\n' + currentRoomKey);
        }).catch(() => {
            alert('复制失败，请手动复制：' + currentRoomKey);
        });
    }
});

// 接收新消息
socket.on('new_message', (data) => {
    const isOwn = data.sender_id === window.currentUserId;
    addMessage(data.content, data.timestamp, isOwn);
});

// 对方离开
socket.on('partner_left', (data) => {
    addSystemMessage('❌ ' + data.message);
    disableChatInput();

    // 5秒后自动返回主页
    setTimeout(() => {
        switchScreen(AppState.INIT);
        clearMessages();
        enableChatInput();
        currentRoomId = null;
    }, 5000);
});

// 自己离开房间
socket.on('left_room', (data) => {
    console.log(data.message);
});

// 错误提示
socket.on('error', (data) => {
    alert('错误: ' + data.message);
});

// 连接断开
socket.on('disconnect', () => {
    console.log('与服务器断开连接');
});

// 页面加载完成
console.log('匿名聊天室已初始化，用户ID:', window.currentUserId);

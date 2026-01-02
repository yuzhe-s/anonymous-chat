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

// 获取DOM元素
const startScreen = document.getElementById('start-screen');
const waitingScreen = document.getElementById('waiting-screen');
const chatScreen = document.getElementById('chat-screen');
const startMatchBtn = document.getElementById('start-match-btn');
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

// 开始匹配
startMatchBtn.addEventListener('click', () => {
    socket.emit('join_queue');
    switchScreen(AppState.WAITING);
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
    switchScreen(AppState.CHATTING);
    clearMessages();
    addSystemMessage('✅ 已匹配到聊天对象，开始聊天吧！');
    enableChatInput();
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

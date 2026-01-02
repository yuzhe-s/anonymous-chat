# 匿名聊天室

一个基于 Flask + Socket.IO 的实时匿名聊天应用，支持随机匹配两个用户进行一对一聊天。

## 功能特性

✅ **随机匹配** - 自动匹配等待中的用户
✅ **实时通信** - 基于 WebSocket 的双向实时消息传输
✅ **匿名聊天** - 使用 UUID 生成匿名身份，保护隐私
✅ **聊天记录** - 所有消息自动保存到数据库
✅ **离开房间** - 用户可随时主动退出聊天
✅ **消息时间** - 每条消息显示发送时间

## 技术栈

- **后端**: Flask + Flask-SocketIO
- **数据库**: SQLite
- **前端**: HTML + CSS + JavaScript
- **实时通信**: Socket.IO

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 3. 测试

打开两个浏览器窗口或使用不同浏览器访问 `http://localhost:5000`，点击"开始匹配"即可体验匹配和聊天功能。

## 项目结构

```
anonymous-chat/
├── app.py                      # Flask 主应用和 SocketIO 事件处理
├── models.py                   # 数据模型 (ChatRoom, Message)
├── config.py                   # 应用配置
├── matching_queue.py           # 匹配队列管理器
├── requirements.txt            # Python 依赖
├── templates/
│   └── index.html             # 前端页面
├── static/
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── chat.js            # WebSocket 客户端逻辑
└── chat.db                    # SQLite 数据库 (自动生成)
```

## 工作原理

1. **用户访问** → 自动生成 8 位 UUID 作为匿名 ID
2. **开始匹配** → 加入等待队列
3. **匹配成功** → 创建 ChatRoom 记录，双方加入 Socket.IO room
4. **发送消息** → 保存到 Message 表，实时广播给对方
5. **离开聊天** → 标记房间为不活跃，通知对方

## Socket.IO 事件

### 客户端发送

- `join_queue` - 加入匹配队列
- `send_message` - 发送消息
- `leave_room_event` - 离开房间

### 服务端发送

- `waiting` - 等待匹配中
- `matched` - 匹配成功
- `new_message` - 接收新消息
- `partner_left` - 对方离开
- `error` - 错误提示

## 数据库模型

### ChatRoom (聊天室)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user1_id | String(100) | 用户1 ID |
| user2_id | String(100) | 用户2 ID |
| created_at | DateTime | 创建时间 |
| is_active | Boolean | 是否活跃 |

### Message (消息)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| room_id | Integer | 房间ID (外键) |
| sender_id | String(100) | 发送者ID |
| content | Text | 消息内容 |
| timestamp | DateTime | 发送时间 |

## 安全性

- ✅ **XSS 防护** - 前端使用 `escapeHtml()` 转义消息内容
- ✅ **消息验证** - 后端限制消息长度（最大 500 字符）
- ✅ **会话安全** - Flask SECRET_KEY 加密 session
- ✅ **SQL 注入防护** - 使用 SQLAlchemy ORM

## 注意事项

1. **开发环境** - 当前配置适用于开发测试，生产环境需要：
   - 配置真实的 SECRET_KEY
   - 使用 PostgreSQL/MySQL 替代 SQLite
   - 配置 HTTPS 和 Nginx 反向代理
   - 使用 Redis 替代内存队列（支持多服务器部署）

2. **匹配队列** - 使用内存存储，服务器重启后队列清空

3. **浏览器兼容性** - 需要支持 WebSocket 的现代浏览器

## 许可证

MIT License

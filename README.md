# 🎭 匿名聊天室

一个基于 Flask + Socket.IO 的实时匿名聊天应用，支持随机匹配两个用户进行一对一聊天。

## ✨ 功能特性

✅ **随机匹配** - 自动匹配等待中的用户
✅ **实时通信** - 基于 WebSocket 的双向实时消息传输
✅ **匿名聊天** - 使用 UUID 生成匿名身份，保护隐私
✅ **聊天记录** - 所有消息自动保存到 PostgreSQL 数据库
✅ **管理后台** - 查看所有聊天记录，支持导出 CSV/JSON
✅ **数据持久化** - 使用 PostgreSQL，重启不丢失数据
✅ **离开房间** - 用户可随时主动退出聊天
✅ **北京时间** - 所有时间戳自动转换为北京时间 (UTC+8)

## 🛠 技术栈

- **后端**: Flask 3.0 + Flask-SocketIO 5.3
- **数据库**: PostgreSQL (生产环境) / SQLite (开发环境)
- **WebSocket**: Socket.IO with eventlet
- **前端**: HTML + CSS + JavaScript
- **部署**: Gunicorn + eventlet worker
- **异步处理**: eventlet 0.37.0

## 🚀 快速开始

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/yuzhe-s/anonymous-chat.git
cd anonymous-chat
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

#### 4. 测试

打开两个浏览器窗口访问 `http://localhost:5000`，点击"开始匹配"即可体验。

### 生产部署

项目已部署在 Render: https://anonymous-chat-4ny5.onrender.com

详细部署指南请查看 [DEPLOY.md](DEPLOY.md)

## 📁 项目结构

```
anonymous-chat/
├── app.py                      # Flask 主应用和 SocketIO 事件处理
├── models.py                   # 数据模型 (ChatRoom, Message)
├── config.py                   # 应用配置（支持 PostgreSQL）
├── matching_queue.py           # 匹配队列管理器
├── wsgi.py                     # WSGI 入口文件（生产环境）
├── requirements.txt            # Python 依赖
├── requirements-prod.txt       # 生产环境额外依赖
├── runtime.txt                 # Python 版本锁定 (3.12)
├── DEPLOY.md                   # 部署指南
├── templates/
│   ├── index.html             # 主页面
│   └── admin.html             # 管理后台页面
├── static/
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── chat.js            # WebSocket 客户端逻辑
└── chat.db                    # SQLite 数据库 (仅本地开发)
```

## 🔄 工作流程

1. **用户访问** → 自动生成 8 位 UUID 作为匿名 ID
2. **开始匹配** → 加入等待队列
3. **匹配成功** → 创建 ChatRoom 记录，双方加入 Socket.IO room
4. **发送消息** → 保存到 PostgreSQL，实时广播给对方
5. **离开聊天** → 标记房间为不活跃，通知对方

## 🔌 Socket.IO 事件

### 客户端 → 服务端

- `join_queue` - 加入匹配队列
- `send_message` - 发送消息
- `leave_room_event` - 离开房间

### 服务端 → 客户端

- `waiting` - 等待匹配中
- `matched` - 匹配成功
- `new_message` - 接收新消息
- `partner_left` - 对方离开
- `error` - 错误提示

## 🗄 数据库模型

### ChatRoom (聊天室)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user1_id | String(100) | 用户1 ID |
| user2_id | String(100) | 用户2 ID |
| created_at | DateTime | 创建时间 (北京时间) |
| is_active | Boolean | 是否活跃 |

### Message (消息)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| room_id | Integer | 房间ID (外键) |
| sender_id | String(100) | 发送者ID |
| content | Text | 消息内容 (最大500字符) |
| timestamp | DateTime | 发送时间 (北京时间) |

## 🔐 管理后台

### 访问地址

```
https://anonymous-chat-4ny5.onrender.com/admin?password=admin123
```

### 功能

- 📊 查看统计数据（总聊天室数、总消息数、活跃房间数）
- 💬 查看所有聊天记录
- 📥 导出 CSV（可用 Excel 打开）
- 📦 导出 JSON（用于数据分析）

### 修改管理员密码

在 Render 设置环境变量：
- Key: `ADMIN_PASSWORD`
- Value: 你的密码

## 🔒 安全性

- ✅ **XSS 防护** - 前端使用 `escapeHtml()` 转义消息内容
- ✅ **消息验证** - 后端限制消息长度（最大 500 字符）
- ✅ **会话安全** - Flask SECRET_KEY 加密 session
- ✅ **SQL 注入防护** - 使用 SQLAlchemy ORM
- ✅ **管理后台保护** - 密码验证访问
- ✅ **数据库连接池优化** - 使用 NullPool 兼容 eventlet

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `SECRET_KEY` | Flask 密钥 | 随机生成 | ✅ 推荐 |
| `DATABASE_URL` | PostgreSQL 连接字符串 | SQLite | ✅ 生产环境 |
| `ADMIN_PASSWORD` | 管理后台密码 | `admin123` | ❌ |
| `PYTHON_VERSION` | Python 版本 | `3.12` | ❌ |
| `WEB_CONCURRENCY` | Worker 数量 | `1` | ❌ |

## 📊 性能参数

### 当前配置（Render 免费版）

- **并发连接**: 50-100 人同时在线
- **同时聊天**: 25-50 对用户
- **月流量**: 100 GB（免费额度）
- **数据库**: PostgreSQL 免费版（90天备份）

### 扩展建议

如需支持更多用户（1000+），建议：
1. 添加 Redis 作为消息队列
2. 增加到 4-8 个 worker
3. 升级到 Render 付费版（$7/月）

## 🐛 常见问题

### Q1: Render 部署后数据库连接失败？

**A**: 检查是否添加了 `DATABASE_URL` 环境变量，并创建了 PostgreSQL 数据库。

### Q2: 匹配一直转圈无法匹配？

**A**: 可能是 Render 启动了多个实例，内存队列不共享。建议设置 `WEB_CONCURRENCY=1`。

### Q3: 重启后数据丢失？

**A**: 确保使用了 PostgreSQL 而不是 SQLite。检查 `DATABASE_URL` 环境变量是否配置。

### Q4: 如何导出聊天记录？

**A**: 访问管理后台，点击"导出 CSV（Excel）"按钮即可。

## 📝 注意事项

1. **生产环境**：
   - ✅ 配置真实的 `SECRET_KEY`
   - ✅ 使用 PostgreSQL 数据库
   - ✅ 修改默认管理员密码
   - ✅ 配置 HTTPS（Render 自动提供）

2. **开发环境**：
   - 本地使用 SQLite，数据存储在 `chat.db`
   - 直接运行 `python app.py` 即可

3. **浏览器兼容性**：
   - 需要支持 WebSocket 的现代浏览器
   - Chrome/Firefox/Safari/Edge 最新版本

## 📄 许可证

MIT License

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/)
- [Socket.IO](https://socket.io/)
- [Render](https://render.com/) - 免费部署平台

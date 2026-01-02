# 🚀 部署指南

本文档介绍如何将匿名聊天室部署到互联网上，让远程用户也能访问。

---

## 方案对比

| 方案 | 费用 | 难度 | WebSocket支持 | 推荐度 |
|------|------|------|---------------|--------|
| Render | 免费 | ⭐ 简单 | ✅ | ⭐⭐⭐⭐⭐ |
| Railway | 免费额度 | ⭐⭐ 中等 | ✅ | ⭐⭐⭐⭐ |
| PythonAnywhere | 免费 | ⭐⭐ 中等 | ❌ 需付费 | ⭐⭐ |
| 自建服务器 | 付费 | ⭐⭐⭐⭐ 困难 | ✅ | ⭐⭐⭐ |

---

## 🎯 方案 1：Render 部署（推荐）

### 为什么选择 Render？
- ✅ 完全免费（无需信用卡）
- ✅ 自动 HTTPS
- ✅ 支持 WebSocket
- ✅ 自动从 Git 部署
- ⚠️ 缺点：15分钟无访问会休眠

### 部署步骤

#### 第一步：上传代码到 GitHub

1. **创建 GitHub 账号**（如果没有）
   - 访问 https://github.com
   - 注册一个免费账号

2. **创建新仓库**
   - 点击右上角 `+` → `New repository`
   - 仓库名：`anonymous-chat`
   - 设置为 `Public`（公开）
   - 点击 `Create repository`

3. **上传代码**

   打开终端，在项目目录执行：
   ```bash
   cd c:\Users\YangFan\anonymous-chat
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/anonymous-chat.git
   git push -u origin main
   ```

#### 第二步：在 Render 部署

1. **注册 Render 账号**
   - 访问 https://render.com
   - 使用 GitHub 账号登录（推荐）

2. **创建新的 Web Service**
   - 点击 `New +` → `Web Service`
   - 选择你的 GitHub 仓库 `anonymous-chat`
   - 点击 `Connect`

3. **配置部署设置**

   填写以下信息：

   - **Name**: `anonymous-chat`（或你喜欢的名字）
   - **Region**: 选择 `Singapore`（离中国最近）
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && pip install -r requirements-prod.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app
     ```

4. **高级设置（Environment）**

   点击 `Advanced` → 添加环境变量：

   - **Key**: `SECRET_KEY`
   - **Value**: `your-random-secret-key-12345`（改成随机字符串）

5. **选择免费计划**
   - Instance Type: `Free`

6. **点击 `Create Web Service`**

7. **等待部署完成**
   - 需要 5-10 分钟
   - 部署成功后会显示你的网址，例如：
     ```
     https://anonymous-chat-xxxx.onrender.com
     ```

#### 第三步：测试

访问你的网址，应该能看到匿名聊天室界面！

---

## 🎯 方案 2：Railway 部署

### 为什么选择 Railway？
- ✅ 每月 $5 免费额度
- ✅ 不会休眠
- ✅ 部署更快
- ⚠️ 需要绑定信用卡（但不会扣费）

### 部署步骤

1. **访问** https://railway.app
2. **用 GitHub 登录**
3. **New Project** → **Deploy from GitHub repo**
4. 选择 `anonymous-chat` 仓库
5. **添加环境变量**：
   - `SECRET_KEY` = 随机字符串
6. **等待部署完成**

---

## 🎯 方案 3：使用内网穿透（临时测试用）

如果你只是想让同学临时测试，可以使用内网穿透工具。

### 使用 ngrok（最简单）

1. **下载 ngrok**
   - 访问 https://ngrok.com
   - 注册并下载 Windows 版本

2. **启动你的应用**
   ```bash
   cd c:\Users\YangFan\anonymous-chat
   python app.py
   ```

3. **在另一个终端运行 ngrok**
   ```bash
   ngrok http 5000
   ```

4. **获取公网地址**
   - ngrok 会显示一个地址，例如：
     ```
     https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app
     ```
   - 把这个地址发给同学即可访问！

⚠️ **注意**：ngrok 免费版每次重启地址都会变化

---

## 🎯 方案 4：使用花生壳（国内更稳定）

1. **下载花生壳客户端**
   - 访问 https://hsk.oray.com
   - 下载并安装

2. **注册账号并实名认证**

3. **创建映射**
   - 内网主机：`127.0.0.1`
   - 内网端口：`5000`
   - 外网端口：自动分配

4. **获取公网域名**
   - 花生壳会给你一个固定域名
   - 同学通过这个域名访问

---

## 📝 部署后的优化建议

### 1. 修改 config.py 支持生产环境

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # 生产环境使用 PostgreSQL
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///chat.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
```

### 2. 使用 Redis 作为消息队列（可选）

在 Render 上添加 Redis 服务，修改 `app.py`：

```python
socketio = SocketIO(app,
                    message_queue='redis://your-redis-url',
                    cors_allowed_origins="*")
```

### 3. 添加数据库持久化

Render 免费版重启后 SQLite 数据会丢失，建议：
- 升级到 Render 付费版（$7/月）使用持久磁盘
- 或使用外部数据库（ElephantSQL 提供免费 PostgreSQL）

---

## ❓ 常见问题

### Q1: 部署后无法访问？
- 检查 Start Command 是否正确
- 查看 Render 的日志（Logs 标签页）
- 确保端口使用 `$PORT` 环境变量

### Q2: WebSocket 连接失败？
- 确认使用 `eventlet` worker：
  ```bash
  gunicorn --worker-class eventlet -w 1 wsgi:app
  ```

### Q3: 免费版服务器休眠怎么办？
- 使用 UptimeRobot（免费）定时 ping 你的网站保持唤醒
- 访问 https://uptimerobot.com
- 添加你的网站 URL，每 5 分钟 ping 一次

### Q4: 如何绑定自己的域名？
- 在域名注册商添加 CNAME 记录
- 指向 Render 提供的域名
- 在 Render 的 Settings 中添加 Custom Domain

---

## 🎓 推荐方案总结

**给同学临时测试** → 使用 **ngrok** 或 **花生壳**

**长期运行（免费）** → 使用 **Render**
- 优点：永久免费、自动 HTTPS
- 缺点：会休眠（可用 UptimeRobot 解决）

**长期运行（付费）** → 使用 **Railway** 或 **Render 付费版**
- 稳定不休眠
- 每月 $5-7

**学习部署知识** → 自己买云服务器（腾讯云/阿里云学生机）
- 最灵活
- 需要学习 Nginx、域名配置等

---

需要我帮你完成具体某个方案的部署吗？告诉我你的选择！
